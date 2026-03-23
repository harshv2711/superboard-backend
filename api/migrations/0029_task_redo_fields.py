from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0028_task_is_marked_completed_by_account_planner_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="status",
            field=models.CharField(
                choices=[
                    ("brief_received", "Brief Received"),
                    ("ideation", "Ideation"),
                    ("designing", "Designing"),
                    ("internal_review", "Internal Review"),
                    ("client_review", "Client Review"),
                    ("revision", "Revision"),
                    ("redo", "Redo"),
                    ("approved", "Approved"),
                    ("published", "Published"),
                ],
                default="brief_received",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="redo_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="task",
            name="redo_no",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="task",
            name="redo_of",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name="redos",
                to="api.task",
            ),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(fields=["redo_of"], name="api_task_redo_of_353d89_idx"),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(fields=["redo_no"], name="api_task_redo_no_f5abbc_idx"),
        ),
    ]
