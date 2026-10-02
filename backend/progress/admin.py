from django.contrib import admin

from .models import Achievement, DailyGoal, ProgressLog


@admin.register(ProgressLog)
class ProgressLogAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "reviews", "new_words", "trainer_total", "trainer_correct", "chat_messages"]
    list_filter = ["date"]


admin.site.register(DailyGoal)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ["user", "key", "unlocked_at", "seen"]
    list_filter = ["key"]
    search_fields = ["user__email"]
