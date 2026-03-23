from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0047_rename_api_negativ_task_id_2b1f5d_idx_api_negativ_task_id_4d7be0_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="TaskAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="task_attachments/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "task",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="attachments", to="api.task"),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="taskattachment",
            index=models.Index(fields=["task"], name="api_taskatt_task_id_a98fe0_idx"),
        ),
        migrations.AddIndex(
            model_name="taskattachment",
            index=models.Index(fields=["created_at"], name="api_taskatt_created_85faaa_idx"),
        ),
    ]
