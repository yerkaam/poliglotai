from django.conf import settings
from django.db import models


class Scenario(models.Model):
    """A short situational dialog (6–10 lines). Edited by the methodologist in the admin."""

    slug = models.SlugField(unique=True)
    title_kk = models.CharField(max_length=60)
    brief_en = models.TextField(help_text="What the AI plays and what the learner should practise.")
    max_turns = models.PositiveSmallIntegerField(default=8)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "chat_scenarios"
        ordering = ["order"]

    def __str__(self):
        return self.title_kk


class Conversation(models.Model):
    class Mode(models.TextChoices):
        DIALOG = "dialog", "Диалог"
        BUILDER = "builder", "Құрастырғыш"
        FREE = "free", "Еркін"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    mode = models.CharField(max_length=10, choices=Mode.choices)
    scenario = models.ForeignKey(Scenario, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    finished = models.BooleanField(default=False)

    class Meta:
        db_table = "conversations"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "Оқушы"
        ASSISTANT = "assistant", "AI"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=Role.choices)
    text = models.TextField()
    # assistant: Kazakh translation of the line and an answer template (hints on request)
    translation_kk = models.TextField(blank=True)
    hint_en = models.CharField(max_length=200, blank=True)
    new_words = models.JSONField(default=list, blank=True)
    # user: whether the sentence was correct and the corrections, each tied to a table cell
    correct = models.BooleanField(null=True)
    corrections = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
        ordering = ["created_at", "id"]
