# Generated by Django 5.1.6 on 2025-02-21 21:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
        ('sales', '0003_rename_quantity_saleitem_stock_quantity'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sale',
            options={'ordering': ['-date']},
        ),
        migrations.RenameField(
            model_name='saleitem',
            old_name='selling_price',
            new_name='price_per_piece',
        ),
        migrations.RenameField(
            model_name='saleitem',
            old_name='stock_quantity',
            new_name='quantity',
        ),
        migrations.RemoveField(
            model_name='sale',
            name='is_credit',
        ),
        migrations.RemoveField(
            model_name='sale',
            name='is_paid',
        ),
        migrations.AddField(
            model_name='sale',
            name='amount_paid',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='sale',
            name='balance',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='sale',
            name='payment_status',
            field=models.CharField(choices=[('Paid', 'Paid'), ('Partial', 'Partial Payment'), ('Credit', 'Credit')], default='Credit', max_length=10),
        ),
        migrations.AddField(
            model_name='sale',
            name='price_per_piece',
            field=models.DecimalField(decimal_places=2, default='0', max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sale',
            name='product',
            field=models.ForeignKey(default='0', on_delete=django.db.models.deletion.CASCADE, to='inventory.product'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sale',
            name='quantity',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='sale',
            name='date',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.DeleteModel(
            name='CreditSale',
        ),
    ]
