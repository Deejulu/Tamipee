from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_product_egg_units'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='inventory_applied',
            field=models.BooleanField(default=False),
        ),
    ]