from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0051_rename_api_clienta_client__8def06_idx_api_clienta_client__045cb3_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="scopeofwork",
            name="type_of_work",
            field=models.ManyToManyField(blank=True, related_name="scope_of_work_items", to="api.typeofwork"),
        ),
    ]
