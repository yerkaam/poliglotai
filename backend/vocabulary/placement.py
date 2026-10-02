"""The placement test: about 20 questions from easy to hard, each tied to a course step.

A step is credited when every question of it is right and every step before it is credited too, so the
learner starts the course where their knowledge ends. Credit only ever adds: a later, weaker run never takes
a step away. Level: A1 once the basic verb table (step 1) is credited, A0 otherwise.
"""

from django.db import transaction

from users.models import Profile

from .course_content import choice
from .models import CourseStep, StepResult

QUESTIONS = [
    # step 1: the basic verb table
    (1, choice("I ___ tea every morning.", "Мен күнде таңертең шай ішемін.", ["drink", "drinks", "drank"], "drink")),
    (1, choice("___ she work in a bank?", "Ол банкте жұмыс істей ме?", ["Do", "Does", "Is"], "Does")),
    (1, choice("We ___ to Almaty last year.", "Біз өткен жылы Алматыға бардық.", ["go", "went", "goed"], "went")),
    (1, choice("They ___ come tomorrow.", "Олар ертең келмейді.", ["don't", "didn't", "won't"], "won't")),
    # step 2: question words
    (2, choice("___ do you live? — In Taraz.", "Қайда тұрасың?", ["What", "Where", "Who"], "Where")),
    (2, choice("___ books do you have?", "Сенде неше кітап бар?", ["How much", "How many", "Which"], "How many")),
    # step 3: to be
    (3, choice("My parents ___ teachers.", "Ата-анам — мұғалім.", ["is", "are", "am"], "are")),
    (3, choice("I ___ tired yesterday.", "Кеше шаршадым.", ["was", "were", "did"], "was")),
    # step 4: prepositions
    (4, choice("The meeting is ___ Monday.", "Кездесу дүйсенбіде.", ["in", "on", "at"], "on")),
    (4, choice("She is ___ work now.", "Ол қазір жұмыста.", ["in", "on", "at"], "at")),
    # step 5: possessives
    (5, choice("Aigerim loves ___ job.", "Айгерім жұмысын жақсы көреді.", ["his", "her", "their"], "her")),
    (5, choice("This bag isn't yours. It's ___ .", "Бұл сөмке сенікі емес, менікі.", ["my", "me", "mine"], "mine")),
    # step 6: irregular verbs
    (6, choice("I ___ my keys. Can you help me?", "Кілттерімді жоғалтып алдым.", ["losed", "lost", "lose"], "lost")),
    (
        6,
        choice(
            "She ___ us English last year.",
            "Ол бізге өткен жылы ағылшын тілін оқытты.",
            ["teached", "taught", "teach"],
            "taught",
        ),
    ),
    # step 7: modals
    (7, choice("You ___ see a doctor.", "Дәрігерге қаралғаның жөн.", ["should", "should to", "shoulds"], "should")),
    (7, choice("Can he ___ ?", "Ол жүзе ала ма?", ["swim", "swims", "to swim"], "swim")),
    # step 8: continuous
    (8, choice("Look! It ___ .", "Қара! Жаңбыр жауып тұр.", ["rains", "is raining", "rained"], "is raining")),
    (
        8,
        choice(
            "At 8 p.m. I ___ TV.",
            "Сағат сегізде теледидар көріп отырдым.",
            ["was watching", "watched", "am watching"],
            "was watching",
        ),
    ),
    # step 9: present perfect
    (9, choice("Have you ever ___ to London?", "Лондонда болып көрдің бе?", ["been", "was", "be"], "been")),
    (9, choice("I ___ this film last week.", "Бұл фильмді өткен аптада көрдім.", ["have seen", "saw", "see"], "saw")),
    # step 10: comparison
    (10, choice("My brother is ___ than me.", "Ағам менен ұзын.", ["taller", "more tall", "tallest"], "taller")),
    (
        10,
        choice("It's the ___ day of my life!", "Бұл — өмірімдегі ең жақсы күн!", ["goodest", "best", "better"], "best"),
    ),
]


def public_questions() -> list[dict]:
    keep = ("type", "prompt", "prompt_kk", "options")
    return [{**{k: q[k] for k in keep}, "step": step} for step, q in QUESTIONS]


def score(answers: list[str]) -> dict:
    right_by_step: dict[int, list[bool]] = {}
    items = []
    for i, (step, q) in enumerate(QUESTIONS):
        given = answers[i] if i < len(answers) else ""
        ok = given.strip() == q["answer"]
        right_by_step.setdefault(step, []).append(ok)
        items.append({"correct": ok, "right": q["answer"]})
    credited = []
    for step in sorted(right_by_step):
        if not all(right_by_step[step]):
            break
        credited.append(step)
    return {
        "items": items,
        "score": sum(1 for item in items if item["correct"]),
        "total": len(QUESTIONS),
        "steps_credited": credited,
        "level": Profile.Level.A1 if credited else Profile.Level.A0,
    }


@transaction.atomic
def apply(user, result: dict) -> None:
    """Credits the steps (as passed, lessons taken) and sets the level; never lowers either."""
    profile, _ = Profile.objects.get_or_create(user=user)
    # Before onboarding the test decides the level; afterwards it can only raise it.
    if not profile.onboarded or result["level"] == Profile.Level.A1:
        profile.level = result["level"]
        profile.save(update_fields=["level"])
    for step in CourseStep.objects.filter(number__in=result["steps_credited"]):
        row, _ = StepResult.objects.get_or_create(user=user, step=step)
        row.passed = True
        row.best_percent = max(row.best_percent, 100)
        row.lessons_done = max(row.lessons_done, len(step.lesson))
        row.save()
