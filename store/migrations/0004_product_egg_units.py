from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_contactmessage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='unit',
            field=models.CharField(choices=[('kg', 'Kilogram'), ('g', 'Gram'), ('piece', 'Piece'), ('dozen', 'Dozen'), ('tray', 'Tray'), ('crate', 'Crate'), ('litre', 'Litre')], default='kg', max_length=20),
        ),
    ]