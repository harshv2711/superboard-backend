from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0034_task_created_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="logo",
            field=models.ImageField(blank=True, null=True, upload_to="client_logos/"),
        ),
    ]
