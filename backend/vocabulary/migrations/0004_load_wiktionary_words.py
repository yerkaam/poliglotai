from django.db import migrations


def forwards(apps, schema_editor):
    from vocabulary.wiktionary import load

    Vocabulary = apps.get_model("vocabulary", "Vocabulary")
    Vocabulary.objects.filter(source="course").update(pos="verb")
    load(Vocabulary)


def backwards(apps, schema_editor):
    apps.get_model("vocabulary", "Vocabulary").objects.filter(source="wiktionary").delete()


class Migration(migrations.Migration):
    dependencies = [("vocabulary", "0003_pos_and_wiktionary_source")]
    operations = [migrations.RunPython(forwards, backwards)]
