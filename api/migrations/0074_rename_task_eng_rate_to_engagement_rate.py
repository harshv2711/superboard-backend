from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0073_task_performance_metrics"),
    ]

    operations = [
        migrations.RenameField(
            model_name="task",
            old_name="eng_rate",
            new_name="engagement_rate",
        ),
    ]
