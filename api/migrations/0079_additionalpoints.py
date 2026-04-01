from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0078_rename_api_task_platform_4eccde_idx_api_task_platfor_002db2_idx"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AdditionalPoints",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("points", models.DecimalField(decimal_places=4, max_digits=12)),
                ("date", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="additional_points",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-date", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="additionalpoints",
            index=models.Index(fields=["user"], name="api_additio_user_id_f87e38_idx"),
        ),
        migrations.AddIndex(
            model_name="additionalpoints",
            index=models.Index(fields=["date"], name="api_additio_date_3d7ea4_idx"),
        ),
    ]
