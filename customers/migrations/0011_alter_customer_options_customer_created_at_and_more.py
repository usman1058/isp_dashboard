# Generated by Django 5.2.1 on 2025-07-06 10:17

import customers.models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0010_remove_reminder_customers_r_status_4a3e24_idx_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customer',
            options={'ordering': ['-join_date'], 'verbose_name': 'Customer', 'verbose_name_plural': 'Customers'},
        ),
        migrations.AddField(
            model_name='customer',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='customer',
            name='id_card_back',
            field=models.ImageField(blank=True, null=True, upload_to=customers.models.customer_id_upload_path, validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png'])], verbose_name='ID Card Back'),
        ),
        migrations.AddField(
            model_name='customer',
            name='id_card_front',
            field=models.ImageField(blank=True, null=True, upload_to=customers.models.customer_id_upload_path, validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png'])], verbose_name='ID Card Front'),
        ),
        migrations.AddField(
            model_name='customer',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='username',
            field=models.CharField(default=django.utils.timezone.now, help_text='Unique username for customer login', max_length=50, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='service_plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='customers.serviceplan'),
        ),
    ]
