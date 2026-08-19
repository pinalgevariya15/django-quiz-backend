import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class CustomPasswordValidator:
    """
    Validator to check that the password contains:
    - At least 6 characters.
    - At least 1 lowercase letter.
    - At least 1 uppercase letter.
    - At least 1 number.
    - At least 1 special character.
    """
    def validate(self, password, user=None):
        if len(password) < 6:
            raise ValidationError(
                _("Password must be at least 6 characters long."),
                code='password_too_short'
            )
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least 1 lowercase letter."),
                code='password_no_lowercase'
            )
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least 1 uppercase letter."),
                code='password_no_uppercase'
            )
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least 1 number."),
                code='password_no_number'
            )
        if not re.search(r'[^a-zA-Z0-9]', password):
            raise ValidationError(
                _("Password must contain at least 1 special character."),
                code='password_no_special'
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 6 characters, 1 lowercase letter, 1 uppercase letter, 1 number, and 1 special character."
        )
