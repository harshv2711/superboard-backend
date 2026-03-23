from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0036_client_accent_color"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="excellence",
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
    ]
