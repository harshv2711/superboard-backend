from django.db import migrations, models


def copy_negative_remark_task_links(apps, schema_editor):
    NegativeRemark = apps.get_model("api", "NegativeRemark")
    NegativeRemarkOnTask = apps.get_model("api", "NegativeRemarkOnTask")

    for remark in NegativeRemark.objects.exclude(task_id=None):
        NegativeRemarkOnTask.objects.get_or_create(
            task_id=remark.task_id,
            negative_remark_id=remark.id,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0044_rename_api_negativ_task_id_7f7dc0_idx_api_negativ_task_id_c9d2c4_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="NegativeRemarkOnTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "negative_remark",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="task_links", to="api.negativeremark"),
                ),
                (
                    "task",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="negative_remark_links", to="api.task"),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="negativeremarkontask",
            constraint=models.UniqueConstraint(fields=("task", "negative_remark"), name="uniq_negative_remark_on_task"),
        ),
        migrations.AddIndex(
            model_name="negativeremarkontask",
            index=models.Index(fields=["task"], name="api_negativ_task_id_2b1f5d_idx"),
        ),
        migrations.AddIndex(
            model_name="negativeremarkontask",
            index=models.Index(fields=["negative_remark"], name="api_negativ_negativ_0e76b1_idx"),
        ),
        migrations.RunPython(copy_negative_remark_task_links, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name="negativeremark",
            name="api_negativ_task_id_c9d2c4_idx",
        ),
        migrations.RemoveField(
            model_name="negativeremark",
            name="task",
        ),
    ]
