# Generated by Django 5.0.1 on 2024-01-09 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_alter_user_dob_alter_user_gender_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='user_contact',
            field=models.CharField(max_length=10, null=True),
        ),
    ]
