# Generated by Django 5.1.6 on 2025-03-03 05:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0013_sale_period_processed'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='status',
            field=models.CharField(choices=[('Active', 'Active'), ('Completed', 'Completed'), ('Damaged', 'Damaged')], default='Active', max_length=20),
        ),
        migrations.CreateModel(
            name='CashTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_date', models.DateTimeField(auto_now_add=True)),
                ('recorded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cash_transactions', to='sales.sale')),
            ],
        ),
        migrations.CreateModel(
            name='CreditTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_date', models.DateTimeField(auto_now_add=True)),
                ('recorded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_transactions', to='sales.sale')),
            ],
        ),
    ]
