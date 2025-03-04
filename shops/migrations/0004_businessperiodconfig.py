# Generated by Django 5.1.6 on 2025-03-02 10:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0003_delete_sellerprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessPeriodConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period_value', models.PositiveIntegerField(default=1)),
                ('period_type', models.CharField(choices=[('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'), ('years', 'Years')], default='weeks', max_length=10)),
                ('last_calculation_date', models.DateField(auto_now_add=True)),
            ],
        ),
    ]
