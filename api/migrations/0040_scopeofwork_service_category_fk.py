from django.db import migrations, models
import django.db.models.deletion


def migrate_scope_service_category(apps, schema_editor):
    ScopeOfWork = apps.get_model("api", "ScopeOfWork")
    ServiceCategory = apps.get_model("api", "ServiceCategory")

    for scope in ScopeOfWork.objects.all():
        raw_value = getattr(scope, "service_category", None)

        category_name = ""
        if isinstance(raw_value, list):
            category_name = next((str(item).strip() for item in raw_value if str(item).strip()), "")
        elif isinstance(raw_value, str):
            category_name = raw_value.strip()
        elif raw_value is not None:
            category_name = str(raw_value).strip()

        if not category_name:
            category_name = "Uncategorized"

        category, _ = ServiceCategory.objects.get_or_create(
            name=category_name,
            defaults={"description": ""},
        )
        scope.service_category_fk_id = category.id
        scope.save(update_fields=["service_category_fk"])


def reverse_scope_service_category(apps, schema_editor):
    ScopeOfWork = apps.get_model("api", "ScopeOfWork")

    for scope in ScopeOfWork.objects.select_related("service_category_fk").all():
        category = getattr(scope, "service_category_fk", None)
        scope.service_category = [category.name] if category else []
        scope.save(update_fields=["service_category"])


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0039_rename_monthly_unit_scopeofwork_total_unit_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="scopeofwork",
            name="service_category_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="api.servicecategory",
            ),
        ),
        migrations.RunPython(migrate_scope_service_category, reverse_scope_service_category),
        migrations.RemoveIndex(
            model_name="scopeofwork",
            name="api_scopeof_service_7ec19f_idx",
        ),
        migrations.RemoveField(
            model_name="scopeofwork",
            name="service_category",
        ),
        migrations.RenameField(
            model_name="scopeofwork",
            old_name="service_category_fk",
            new_name="service_category",
        ),
        migrations.AlterField(
            model_name="scopeofwork",
            name="service_category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="scope_of_work_items",
                to="api.servicecategory",
            ),
        ),
        migrations.AlterModelOptions(
            name="scopeofwork",
            options={"ordering": ["client__name", "service_category__name", "deliverable_name"]},
        ),
        migrations.AddIndex(
            model_name="scopeofwork",
            index=models.Index(fields=["service_category"], name="api_scopeof_service_8ccda8_idx"),
        ),
    ]
