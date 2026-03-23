from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0041_rename_api_scopeof_service_8ccda8_idx_api_scopeof_service_7c5d8c_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="is_marked_completed_by_superadmin",
            field=models.BooleanField(default=False),
        ),
    ]
