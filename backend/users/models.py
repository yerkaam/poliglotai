from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        Profile.objects.get_or_create(user=user)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=80)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email


class Profile(models.Model):
    class Level(models.TextChoices):
        A0 = "A0", "A0 — нөлден"
        A1 = "A1", "A1 — мектеп деңгейі"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    level = models.CharField(max_length=2, choices=Level.choices, default=Level.A0)
    daily_new_limit = models.PositiveSmallIntegerField(default=10)  # 5, 10, 15 or 20 (SRS-07)
    daily_minutes = models.PositiveSmallIntegerField(default=15)
    onboarded = models.BooleanField(default=False)

    class Meta:
        db_table = "profiles"

    def __str__(self):
        return f"Profile({self.user_id})"
