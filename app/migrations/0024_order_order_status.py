# Generated by Django 5.0.1 on 2024-02-13 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0023_alter_billingaddress_contact_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='order_status',
            field=models.CharField(blank=True, choices=[('created', 'Created'), ('in process', 'In Process'), ('out for delivery', 'Out For Delivery'), ('delivered', 'Delivered')], max_length=50, null=True),
        ),
    ]
