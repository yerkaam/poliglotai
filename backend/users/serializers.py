from django.contrib.auth import password_validation
from rest_framework import serializers

from .models import Profile, User

REMINDER_HOURS = [8, 12, 18, 19, 20, 21]
EMAIL_TAKEN = "Бұл поштамен аккаунт бұрыннан бар. Кіріп көріңіз."


class ProfileSerializer(serializers.ModelSerializer):
    daily_new_limit = serializers.ChoiceField(choices=[5, 10, 15, 20])
    reminder_hour = serializers.ChoiceField(choices=REMINDER_HOURS, required=False)

    class Meta:
        model = Profile
        fields = ["level", "daily_new_limit", "daily_minutes", "onboarded", "reminder_enabled", "reminder_hour"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "name", "email_verified", "is_teacher", "profile"]
        read_only_fields = ["is_teacher"]


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    accept_terms = serializers.BooleanField()

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            # AUTH-03: a clear error for an email that is already taken.
            raise serializers.ValidationError(EMAIL_TAKEN)
        return value

    def validate_accept_terms(self, value):
        if not value:
            raise serializers.ValidationError("Пайдалану шарттарымен келісу керек.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Құпиясөздер сәйкес емес."})
        password_validation.validate_password(attrs["password"])
        return attrs

    def create(self, validated):
        return User.objects.create_user(
            email=validated["email"], password=validated["password"], name=validated["name"].strip()
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    remember = serializers.BooleanField(default=False)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField()

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value


class VerifyEmailSerializer(serializers.Serializer):
    code = serializers.RegexField(r"^\s*\d{6}\s*$", error_messages={"invalid": "Код 6 саннан тұрады."})
