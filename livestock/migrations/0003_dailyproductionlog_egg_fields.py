from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('livestock', '0002_dailyfeedlog_dailyproductionlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyproductionlog',
            name='damaged_count',
            field=models.PositiveIntegerField(default=0, help_text='Cracked, dirty, or otherwise unsellable eggs from the batch.'),
        ),
        migrations.AddField(
            model_name='dailyproductionlog',
            name='egg_count',
            field=models.PositiveIntegerField(blank=True, help_text='Optional for layer production: total eggs collected before sorting.', null=True),
        ),
        migrations.AlterField(
            model_name='dailyproductionlog',
            name='unit',
            field=models.CharField(choices=[('crates', 'Crates'), ('tray', 'Tray'), ('crate', 'Crate'), ('kg', 'kg'), ('pieces', 'Pieces'), ('litres', 'Litres')], default='crates', max_length=20),
        ),
    ]