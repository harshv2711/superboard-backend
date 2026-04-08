from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0081_dedupe_clientmonthlyamount_and_add_unique_constraint"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="client",
            constraint=models.UniqueConstraint(Lower("name"), name="uniq_client_name_ci"),
        ),
    ]
