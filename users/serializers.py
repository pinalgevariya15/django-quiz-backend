from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError

from users.models import PasswordResetCode

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return email

    def validate(self, data):
        # Create a temp user instance to validate password with default/custom validators
        user = User(email=data.get('email'))
        try:
            validate_password(data.get('password'), user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)  # email is primary login key, profile can update names
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'date_joined')


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        email = value.strip().lower()
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("There is no user registered with this email address.")
        return email


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(max_length=6, min_length=6, required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate_email(self, value):
        email = value.strip().lower()
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("There is no user registered with this email address.")
        return email

    def validate(self, data):
        email = data.get('email')
        code = data.get('code')
        password = data.get('password')

        if not email or not code:
            return data

        try:
            user = User.objects.get(email=email.strip().lower())
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "There is no user registered with this email address."})

        # Fetch the latest generated code for this user
        reset_code = PasswordResetCode.objects.filter(user=user).order_by('-created_at').first()

        if not reset_code:
            raise serializers.ValidationError({"code": "No password reset code has been requested for this user."})

        if reset_code.is_used:
            raise serializers.ValidationError({"code": "This verification code has already been used."})

        if reset_code.is_expired():
            raise serializers.ValidationError({"code": "This verification code has expired."})

        if reset_code.code != code:
            raise serializers.ValidationError({"code": "Invalid verification code."})

        # Validate password complexity
        try:
            validate_password(password, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        self.context['user'] = user
        self.context['reset_code'] = reset_code
        return data

    def save(self):
        user = self.context['user']
        reset_code = self.context['reset_code']
        password = self.validated_data['password']
        
        # Update user's password
        user.set_password(password)
        user.save()
        
        # Mark code as used
        reset_code.is_used = True
        reset_code.save()
        
        return user


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
        extra_kwargs = {
            'date_joined': {'read_only': True}
        }

    def validate_email(self, value):
        email = value.strip().lower()
        # Exclude current instance in case of PUT/PATCH updates
        qs = User.objects.filter(email=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return email

    def validate(self, data):
        password = data.get('password')
        if password:
            # Validate password complexity
            user = self.instance or User(email=data.get('email'))
            try:
                validate_password(password, user=user)
            except DjangoValidationError as e:
                raise serializers.ValidationError({"password": list(e.messages)})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        email = validated_data.pop('email').strip().lower()
        
        user = User.objects.create_user(
            email=email,
            password=password,
            **validated_data
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        email = validated_data.get('email')
        if email:
            validated_data['email'] = email.strip().lower()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
