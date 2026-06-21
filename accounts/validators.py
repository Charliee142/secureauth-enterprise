import re

from django.core.exceptions import ValidationError


class ComplexPasswordValidator:
    """Enforces SEC-008: min 12 chars, upper, lower, digit, symbol."""

    min_length = 12

    def validate(self, password, user=None):
        errors = []
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long.")
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit.")
        if not re.search(r"[^\w\s]", password):
            errors.append("Password must contain at least one symbol.")
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return (
            f"Your password must be at least {self.min_length} characters and include "
            "an uppercase letter, a lowercase letter, a digit, and a symbol."
        )
