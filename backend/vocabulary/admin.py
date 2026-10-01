from django.contrib import admin

from .models import CourseStep, StepResult, Vocabulary


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ["word", "translation_kk", "ipa", "past_form", "is_irregular", "course_step", "topic", "source"]
    list_filter = ["is_irregular", "is_verb", "course_step", "topic", "source"]
    search_fields = ["word", "translation_kk"]
    list_editable = ["translation_kk"]


@admin.register(CourseStep)
class CourseStepAdmin(admin.ModelAdmin):
    list_display = ["number", "title_kk", "title_en", "is_open"]
    list_editable = ["is_open"]
    fields = ["number", "title_kk", "title_en", "description_kk", "is_open", "grammar_en", "lesson", "exercises"]


@admin.register(StepResult)
class StepResultAdmin(admin.ModelAdmin):
    list_display = ["user", "step", "best_percent", "passed", "updated_at"]
    list_filter = ["step", "passed"]
    search_fields = ["user__email"]
