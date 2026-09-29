from django.core.exceptions import ValidationError


class HasDigitValidator:
    """AUTH-02: a password needs at least one digit."""

    def validate(self, password, user=None):
        if not any(ch.isdigit() for ch in password):
            raise ValidationError("Құпиясөзде кемінде 1 сан болуы керек.", code="password_no_digit")

    def get_help_text(self):
        return "Кемінде 1 сан."
