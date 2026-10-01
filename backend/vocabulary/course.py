"""The course map for one learner: which steps are open, done or still locked.

Step 1 is always open. A step is done when the learner passed its check (80%) and started at least 70% of its
words (steps without a check or without words skip that part). The next published step then opens.
"""

from dataclasses import dataclass

from django.db.models import Count

from srs.models import UserVocabulary

from . import forms
from .models import CourseStep, StepResult, Vocabulary

PASS_PERCENT = 80
WORDS_STARTED_PERCENT = 70


@dataclass
class StepState:
    step: CourseStep
    status: str  # done | open | locked | soon
    words_total: int
    words_started: int
    words_learned: int
    quiz_best: int | None
    quiz_passed: bool

    @property
    def unlocked(self) -> bool:
        return self.status in {"open", "done"}

    @property
    def percent(self) -> int:
        """Word progress: learned words count fully, words in progress count half."""
        if not self.words_total:
            return 100 if self.status == "done" else 0
        return round(100 * (self.words_learned + 0.5 * (self.words_started - self.words_learned)) / self.words_total)

    def as_dict(self) -> dict:
        s = self.step
        return {
            "number": s.number,
            "title_kk": s.title_kk,
            "title_en": s.title_en,
            "description_kk": s.description_kk,
            "status": self.status,
            "words_total": self.words_total,
            "words_started": self.words_started,
            "words_learned": self.words_learned,
            "words_needed": words_needed(self.words_total),
            "percent": self.percent,
            "has_lesson": bool(s.lesson),
            "quiz_total": len(s.exercises),
            "quiz_best": self.quiz_best,
            "quiz_passed": self.quiz_passed,
        }


def words_needed(total: int) -> int:
    return -(-total * WORDS_STARTED_PERCENT // 100)  # ceiling


def _per_step(queryset, field: str) -> dict[int, int]:
    return {row[field]: row["n"] for row in queryset.values(field).annotate(n=Count("id")) if row[field]}


def course_state(user) -> list[StepState]:
    totals = _per_step(Vocabulary.objects.all(), "course_step")
    mine = UserVocabulary.objects.filter(user=user)
    started = _per_step(mine, "vocabulary__course_step")
    learned = _per_step(
        mine.filter(status__in=[UserVocabulary.Status.LEARNED, UserVocabulary.Status.KNOWN]), "vocabulary__course_step"
    )
    results = {r.step_id: r for r in StepResult.objects.filter(user=user)}

    states = []
    previous_done = True
    for step in CourseStep.objects.all():
        result = results.get(step.id)
        total = totals.get(step.id, 0)
        quiz_ok = not step.exercises or bool(result and result.passed)
        words_ok = started.get(step.id, 0) >= words_needed(total)
        if not step.is_open:
            status = "soon"
        elif not previous_done:
            status = "locked"
        else:
            status = "done" if quiz_ok and words_ok else "open"
        previous_done = status == "done"
        states.append(
            StepState(
                step=step,
                status=status,
                words_total=total,
                words_started=started.get(step.id, 0),
                words_learned=learned.get(step.id, 0),
                quiz_best=result.best_percent if result else None,
                quiz_passed=bool(result and result.passed),
            )
        )
    return states


def unlocked_steps(user) -> list[CourseStep]:
    return [s.step for s in course_state(user) if s.unlocked]


def done_steps(user) -> list[CourseStep]:
    return [s.step for s in course_state(user) if s.status == "done"]


def public_exercises(step: CourseStep) -> list[dict]:
    """The check without its answers."""
    keep = ("type", "prompt", "prompt_kk", "options")
    return [{k: e[k] for k in keep if k in e} for e in step.exercises]


def is_right(exercise: dict, answer: str) -> bool:
    if exercise["type"] == "choice":
        return answer.strip() == exercise["answer"]
    return any(forms.is_correct(answer, accepted) for accepted in exercise["answers"])


def right_answer(exercise: dict) -> str:
    return exercise["answer"] if exercise["type"] == "choice" else exercise["answers"][0]


def check(user, step: CourseStep, answers: list[str]) -> dict:
    exercises = step.exercises
    items = []
    for i, exercise in enumerate(exercises):
        given = answers[i] if i < len(answers) else ""
        items.append({"correct": is_right(exercise, given), "right": right_answer(exercise)})
    score = sum(1 for item in items if item["correct"])
    percent = round(100 * score / len(exercises)) if exercises else 100
    passed = percent >= PASS_PERCENT

    before = {s.step.number for s in course_state(user) if s.unlocked}
    result, _ = StepResult.objects.get_or_create(user=user, step=step)
    result.best_percent = max(result.best_percent, percent)
    result.passed = result.passed or passed
    result.save()
    after = course_state(user)
    opened = [s.step.number for s in after if s.unlocked and s.step.number not in before]
    state = next(s for s in after if s.step.id == step.id)
    return {
        "items": items,
        "score": score,
        "total": len(exercises),
        "percent": percent,
        "passed": passed,
        "step": state.as_dict(),
        "opened_step": opened[0] if opened else None,
    }
