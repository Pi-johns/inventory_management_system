# Generated by Django 5.1.6 on 2025-02-23 12:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0008_sale_balance_sale_grand_total_sale_payment_status_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='saleitem',
            old_name='price_per_piece',
            new_name='price',
        ),
    ]
