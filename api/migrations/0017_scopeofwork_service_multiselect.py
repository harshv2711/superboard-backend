from django.db import migrations, models


def migrate_service_to_json_list(apps, schema_editor):
    ScopeOfWork = apps.get_model("api", "ScopeOfWork")
    for item in ScopeOfWork.objects.all().iterator():
        raw_service = item.service
        if isinstance(raw_service, list):
            normalized = raw_service
        elif raw_service:
            normalized = [str(raw_service)]
        else:
            normalized = []
        item.service_json = normalized
        item.save(update_fields=["service_json"])


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0016_alter_scopeofwork_service"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="scopeofwork",
            name="api_scopeof_service_c9e84e_idx",
        ),
        migrations.AddField(
            model_name="scopeofwork",
            name="service_json",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(migrate_service_to_json_list, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="scopeofwork",
            name="service",
        ),
        migrations.RenameField(
            model_name="scopeofwork",
            old_name="service_json",
            new_name="service",
        ),
        migrations.AddIndex(
            model_name="scopeofwork",
            index=models.Index(fields=["service"], name="api_scopeof_service_c9e84e_idx"),
        ),
    ]
