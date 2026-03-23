from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0035_client_logo"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="accent_color",
            field=models.CharField(blank=True, default="", max_length=7),
        ),
    ]
