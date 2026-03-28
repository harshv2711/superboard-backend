from django.db import migrations


def sync_stage_from_completion_flags(apps, schema_editor):
    Task = apps.get_model("api", "Task")

    for task in Task.objects.all().iterator():
        if getattr(task, "is_marked_completed_by_superadmin", False) or getattr(task, "is_marked_completed_by_account_planner", False):
            task.stage = "approved"
        elif getattr(task, "is_marked_completed_by_art_director", False):
            task.stage = "approved_by_art_director_waiting_for_approval"
        elif getattr(task, "is_marked_completed_by_designer", False):
            task.stage = "complete"
        elif not task.stage:
            task.stage = "backlog"
        task.save(update_fields=["stage"])


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0071_alter_task_stage_choices"),
    ]

    operations = [
        migrations.RunPython(sync_stage_from_completion_flags, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="task",
            name="is_marked_completed_by_account_planner",
        ),
        migrations.RemoveField(
            model_name="task",
            name="is_marked_completed_by_art_director",
        ),
        migrations.RemoveField(
            model_name="task",
            name="is_marked_completed_by_designer",
        ),
        migrations.RemoveField(
            model_name="task",
            name="is_marked_completed_by_superadmin",
        ),
    ]
