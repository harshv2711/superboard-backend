from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0049_rename_api_taskatt_task_id_a98fe0_idx_api_taskatt_task_id_142d80_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClientAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="client_attachments/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "client",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="attachments", to="api.client"),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="clientattachment",
            index=models.Index(fields=["client"], name="api_clienta_client__8def06_idx"),
        ),
        migrations.AddIndex(
            model_name="clientattachment",
            index=models.Index(fields=["created_at"], name="api_clienta_created_69dcec_idx"),
        ),
    ]
