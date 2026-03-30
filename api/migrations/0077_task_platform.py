from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0076_alter_task_stage_display_names"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="platform",
            field=models.CharField(
                blank=True,
                choices=[
                    ("instagram", "Instagram"),
                    ("facebook", "Facebook"),
                    ("linkedin", "LinkedIn"),
                    ("x", "X"),
                    ("youtube", "YouTube"),
                    ("tiktok", "TikTok"),
                    ("pinterest", "Pinterest"),
                    ("snapchat", "Snapchat"),
                    ("threads", "Threads"),
                    ("whatsapp", "WhatsApp"),
                ],
                default="",
                max_length=32,
            ),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(fields=["platform"], name="api_task_platform_4eccde_idx"),
        ),
    ]
