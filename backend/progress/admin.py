from django.contrib import admin

from .models import DailyGoal, ProgressLog


@admin.register(ProgressLog)
class ProgressLogAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "reviews", "new_words", "trainer_total", "trainer_correct", "chat_messages"]
    list_filter = ["date"]


admin.site.register(DailyGoal)
