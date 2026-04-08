from django.db import migrations, models


def dedupe_client_monthly_amounts(apps, schema_editor):
    ClientMonthlyAmount = apps.get_model("api", "ClientMonthlyAmount")

    seen = set()
    duplicate_ids = []

    for row in ClientMonthlyAmount.objects.order_by("client_id", "date", "-updated_at", "-id"):
        key = (row.client_id, row.date)
        if key in seen:
            duplicate_ids.append(row.id)
            continue
        seen.add(key)

    if duplicate_ids:
        ClientMonthlyAmount.objects.filter(id__in=duplicate_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0080_rename_api_additio_user_id_f87e38_idx_api_additio_user_id_4e9f4f_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(dedupe_client_monthly_amounts, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="clientmonthlyamount",
            constraint=models.UniqueConstraint(
                fields=("client", "date"),
                name="uniq_client_monthly_amount_client_date",
            ),
        ),
    ]
