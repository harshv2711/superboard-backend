from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0042_task_is_marked_completed_by_superadmin"),
    ]

    operations = [
        migrations.CreateModel(
            name="NegativeRemark",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("remark_name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("point", models.DecimalField(decimal_places=4, default=0, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "task",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="negative_remarks", to="api.task"),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="negativeremark",
            index=models.Index(fields=["task"], name="api_negativ_task_id_7f7dc0_idx"),
        ),
        migrations.AddIndex(
            model_name="negativeremark",
            index=models.Index(fields=["remark_name"], name="api_negativ_remark__2b7d3c_idx"),
        ),
        migrations.AddIndex(
            model_name="negativeremark",
            index=models.Index(fields=["point"], name="api_negativ_point_6b20ff_idx"),
        ),
    ]
