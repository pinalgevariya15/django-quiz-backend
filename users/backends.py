from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()

class CaseInsensitiveModelBackend(ModelBackend):
    """
    Custom authentication backend that permits case-insensitive email logins.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
            
        if username is None:
            return None
            
        try:
            # Match using iexact to handle cases like user@Example.com vs user@example.com
            user = User.objects.get(**{f"{User.USERNAME_FIELD}__iexact": username})
        except User.DoesNotExist:
            # Run set_password to match verification processing times and mitigate timing attacks
            User().set_password(password)
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
