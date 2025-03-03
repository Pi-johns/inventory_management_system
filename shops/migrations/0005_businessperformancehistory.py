# Generated by Django 5.1.6 on 2025-03-02 18:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0004_businessperiodconfig'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessPerformanceHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('total_cash_sales', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('total_credit_sales', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('total_partial_payments', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('total_profit', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('carried_forward_credit', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
            ],
        ),
    ]
