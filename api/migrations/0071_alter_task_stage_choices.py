from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0070_task_monthly_post_impression"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="stage",
            field=models.CharField(
                choices=[
                    ("backlog", "Backlog"),
                    ("on_going", "Ongoing"),
                    ("complete", "Complete"),
                    (
                        "approved_by_art_director_waiting_for_approval",
                        "Approved By Art Director/ Waiting for approval",
                    ),
                    ("approved", "Approved"),
                ],
                default="backlog",
                max_length=64,
            ),
        ),
    ]
