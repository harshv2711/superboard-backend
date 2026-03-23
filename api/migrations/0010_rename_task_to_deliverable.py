from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0009_scopeofwork_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="scopeofwork",
            old_name="task",
            new_name="deliverable",
        ),
        migrations.AlterModelOptions(
            name="scopeofwork",
            options={"ordering": ["client__name", "service", "deliverable"]},
        ),
        migrations.RemoveIndex(
            model_name="scopeofwork",
            name="api_scopeof_task_3b249c_idx",
        ),
        migrations.AddIndex(
            model_name="scopeofwork",
            index=models.Index(fields=["deliverable"], name="api_scopeof_deliverable_idx"),
        ),
    ]
