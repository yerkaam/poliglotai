from django.db import migrations


def forwards(apps, schema_editor):
    from vocabulary.seed import seed

    seed(apps.get_model("vocabulary", "CourseStep"), apps.get_model("vocabulary", "Vocabulary"))


class Migration(migrations.Migration):
    dependencies = [("vocabulary", "0001_initial")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
