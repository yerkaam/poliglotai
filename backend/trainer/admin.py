from django.contrib import admin

from .models import TrainerAttempt


@admin.register(TrainerAttempt)
class TrainerAttemptAdmin(admin.ModelAdmin):
    list_display = ["user", "vocabulary", "pronoun", "tense", "form", "correct", "created_at"]
    list_filter = ["correct", "tense", "form"]
