from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0074_rename_task_eng_rate_to_engagement_rate"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="task",
            name="monthly_post_impression",
        ),
    ]
