import secrets

from django.conf import settings
from django.db import models

# No look-alike characters (0/O, 1/I/L): the code is read aloud in class and typed on phones.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6


def new_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


class Group(models.Model):
    """A teacher's class. Learners join with its code and can leave at any time."""

    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="taught_groups")
    name = models.CharField(max_length=80)
    code = models.CharField(max_length=CODE_LENGTH, unique=True, default=new_code)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "class_groups"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Membership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "class_memberships"
        unique_together = [("group", "student")]
