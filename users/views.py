import random
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.utils import swagger_auto_schema

from users.models import PasswordResetCode

from users.serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    AdminUserSerializer
)

User = get_user_model()

@swagger_auto_schema(tags=['auth'])
class SwaggerTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Validates credentials and returns JWT access + refresh tokens.
    """
    pass


@swagger_auto_schema(tags=['auth'])
class SwaggerTokenRefreshView(TokenRefreshView):
    """
    POST /api/auth/refresh/
    Accepts refresh token and returns a new access token.
    """
    pass


@swagger_auto_schema(tags=['auth'])
class RegistrationView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Registers a new user and returns their profile without returning JWT tokens.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        name = f"{user.first_name} {user.last_name}".strip() or "User"
        user_data = {
            "id": user.id,
            "name": name,
            "email": user.email
        }
        return Response([user_data], status=status.HTTP_201_CREATED)


class ForgotPasswordView(APIView):
    """
    POST /api/auth/forgot-password/
    Generates a 6-digit password reset code and emails it to the user.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['auth'],
        request_body=ForgotPasswordSerializer,
        responses={
            200: 'Password reset code has been sent to your email.',
            400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        # Generate a random 6-digit code
        code = f"{random.randint(100000, 999999)}"

        # Save code to the database
        PasswordResetCode.objects.create(user=user, code=code)

        # Send mail (will print to console as configured in settings)
        subject = "Reset Your Quiz Backend Password"
        message = (
            f"Hello,\n\n"
            f"You requested a password reset. Please use the following 6-digit verification code to reset your password:\n\n"
            f"Verification Code: {code}\n\n"
            f"This code will expire in 15 minutes.\n\n"
            f"If you did not request this, please ignore this email.\n"
        )
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )

        response_data = {
            "message": "Password reset instructions have been sent to your email."
        }
        
        # Include code in development response for testing convenience
        if settings.DEBUG:
            response_data["_debug"] = {
                "code": code
            }

        return Response(response_data, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """
    POST /api/auth/reset-password/
    Verifies the 6-digit verification code and resets the user's password.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['auth'],
        request_body=ResetPasswordSerializer,
        responses={
            200: 'Your password has been successfully reset.',
            #400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Your password has been successfully reset."},
            status=status.HTTP_200_OK
        )


@swagger_auto_schema(tags=['admin'])
class AdminUserViewSet(viewsets.ModelViewSet):
    """
    GET/POST/PUT/PATCH/DELETE /api/admin/users/
    Admin-only endpoint for managing users.
    """
    queryset = User.objects.all().order_by('id')
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
