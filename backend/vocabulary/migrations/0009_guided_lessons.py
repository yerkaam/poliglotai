from django.db import migrations


def forwards(apps, schema_editor):
    # Step 1 split into short lessons; every lesson gets practice questions.
    from vocabulary.course_content import apply

    apply(apps.get_model("vocabulary", "CourseStep"), apps.get_model("vocabulary", "Vocabulary"))


class Migration(migrations.Migration):
    dependencies = [("vocabulary", "0008_lesson_progress")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
