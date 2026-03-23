from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0045_negativeremarkontask_and_remove_task_from_negativeremark"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="task",
            name="api_task_status_2aef03_idx",
        ),
        migrations.RemoveField(
            model_name="task",
            name="status",
        ),
    ]
