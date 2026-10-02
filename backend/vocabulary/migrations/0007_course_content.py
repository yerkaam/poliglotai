from django.db import migrations


def forwards(apps, schema_editor):
    from vocabulary.course_content import apply

    apply(apps.get_model("vocabulary", "CourseStep"), apps.get_model("vocabulary", "Vocabulary"))


class Migration(migrations.Migration):
    dependencies = [("vocabulary", "0006_course_lessons")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
