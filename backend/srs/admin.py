from django.contrib import admin

from .models import UserVocabulary


@admin.register(UserVocabulary)
class UserVocabularyAdmin(admin.ModelAdmin):
    list_display = ["user", "vocabulary", "status", "stage", "next_review_date", "lapses"]
    list_filter = ["status", "stage"]
    search_fields = ["user__email", "vocabulary__word"]
