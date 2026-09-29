from django.contrib import admin

from .models import Conversation, Message, Scenario


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ["title_kk", "slug", "max_turns", "order", "is_active"]
    list_editable = ["order", "is_active"]
    prepopulated_fields = {"slug": ["title_kk"]}


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ["role", "text", "correct", "corrections", "new_words", "created_at"]
    fields = readonly_fields


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "mode", "scenario", "finished", "created_at"]
    list_filter = ["mode", "scenario", "finished"]
    inlines = [MessageInline]
