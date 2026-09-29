from django.db import migrations

SCENARIOS = [
    ("meet", "Танысу", "You meet the learner at a friend's party. Ask their name, where they live, what they do "
     "and what they like.", 1),
    ("cafe", "Кафеде", "You are a friendly waiter in a café in Almaty. Take the learner's order, ask what they "
     "usually drink and what they did today.", 2),
    ("airport", "Әуежайда", "You are a passenger sitting next to the learner at the airport. Ask where they will "
     "go, why, and what they will do there.", 3),
    ("shop", "Дүкенде", "You are a shop assistant in a clothes shop. Help the learner buy something; ask what "
     "they want, what they like and whether they will pay by card.", 4),
    ("interview", "Сұхбат", "You interview the learner for a simple job. Ask where they work now, what they did "
     "before and what they will do in the new job.", 5),
]


def forwards(apps, schema_editor):
    Scenario = apps.get_model("chat", "Scenario")
    for slug, title, brief, order in SCENARIOS:
        Scenario.objects.update_or_create(slug=slug, defaults={"title_kk": title, "brief_en": brief, "order": order})


class Migration(migrations.Migration):
    dependencies = [("chat", "0002_initial")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
