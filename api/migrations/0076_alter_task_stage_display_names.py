from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0075_remove_task_monthly_post_impression"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="stage",
            field=models.CharField(
                choices=[
                    ("backlog", "Initiate"),
                    ("on_going", "Ongoing"),
                    ("complete", "Complete"),
                    ("approved_by_art_director_waiting_for_approval", "Approved By Art Director"),
                    ("approved", "Approved by Client"),
                ],
                default="backlog",
                max_length=64,
            ),
        ),
    ]
