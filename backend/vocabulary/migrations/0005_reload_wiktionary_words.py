from django.db import migrations


def forwards(apps, schema_editor):
    # The dataset grew (second source: the reversed Kazakh dictionary); reload it where 0004 already ran.
    from vocabulary.wiktionary import load

    load(apps.get_model("vocabulary", "Vocabulary"))


class Migration(migrations.Migration):
    dependencies = [("vocabulary", "0004_load_wiktionary_words")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
