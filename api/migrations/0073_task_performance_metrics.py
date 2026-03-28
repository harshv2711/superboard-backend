from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0072_remove_task_completion_flags"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="ctr",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name="task",
            name="eng_rate",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name="task",
            name="impressions",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="task",
            name="promotion_type",
            field=models.CharField(
                choices=[("organic", "Organic"), ("sponsored", "Sponsored")],
                default="organic",
                max_length=16,
            ),
        ),
    ]
