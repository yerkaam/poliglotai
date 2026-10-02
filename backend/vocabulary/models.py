from django.conf import settings
from django.db import models


class CourseStep(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    title_kk = models.CharField(max_length=120)
    title_en = models.CharField(max_length=120)
    description_kk = models.TextField(blank=True)
    is_open = models.BooleanField(
        "published",
        default=False,
        help_text="The step's content is ready. Learners still unlock published steps one by one.",
    )
    intro_kk = models.TextField(blank=True, help_text="What the learner will be able to do after this step.")
    # Short lessons, one idea each, taken one after another:
    # [{"title_kk": str, "text_kk": str, "examples": [{"en": str, "kk": str}],
    #   "practice": [{"prompt": str, "prompt_kk": str, "options": [str], "answer": str, "why_kk": str}]}]
    lesson = models.JSONField(default=list, blank=True)
    # [{"type": "choice", "prompt": str, "prompt_kk": str, "options": [str], "answer": str}
    #  | {"type": "input", "prompt": str, "prompt_kk": str, "answers": [str]}]
    exercises = models.JSONField(default=list, blank=True)
    grammar_en = models.CharField(
        max_length=300, blank=True, help_text="What the AI tutor may use once the learner has completed this step."
    )

    class Meta:
        db_table = "course_steps"
        ordering = ["number"]

    def __str__(self):
        return f"{self.number}. {self.title_kk}"


class Vocabulary(models.Model):
    class Source(models.TextChoices):
        COURSE = "course", "Курс"
        CHAT = "chat", "AI-чат"
        WIKTIONARY = "wiktionary", "Wiktionary (CC BY-SA)"

    word = models.CharField(max_length=60, unique=True)
    translation_kk = models.CharField(max_length=120)
    ipa = models.CharField(max_length=60, blank=True)
    is_verb = models.BooleanField(default=True)
    pos = models.CharField("part of speech", max_length=10, blank=True)
    past_form = models.CharField(
        max_length=60, blank=True, help_text="Only for irregular verbs, or a regular verb with an unusual spelling."
    )
    is_irregular = models.BooleanField(default=False)
    example_en = models.CharField(max_length=200, blank=True)
    example_kk = models.CharField(max_length=200, blank=True)
    topic = models.CharField(max_length=40, default="verbs")
    course_step = models.ForeignKey(CourseStep, null=True, blank=True, on_delete=models.SET_NULL)
    frequency_rank = models.PositiveSmallIntegerField(default=1000)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.COURSE)

    class Meta:
        db_table = "vocabulary"
        ordering = ["frequency_rank", "word"]
        verbose_name_plural = "vocabulary"

    def __str__(self):
        return self.word

    @property
    def past(self) -> str:
        from .forms import past_simple

        return past_simple(self.word, self.past_form)


class StepResult(models.Model):
    """How far the learner got in a step: lessons taken and the best check score. A pass opens the next step."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="step_results")
    step = models.ForeignKey(CourseStep, on_delete=models.CASCADE)
    lessons_done = models.PositiveSmallIntegerField(default=0)
    best_percent = models.PositiveSmallIntegerField(default=0)
    passed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "step_results"
        unique_together = [("user", "step")]
