# Generated by Django 5.0.2 on 2024-03-02 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investments', '0005_alter_withdrawalrequest_to_address'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='token_sent_at',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='verification_token',
        ),
        migrations.AlterField(
            model_name='customuser',
            name='email_verified',
            field=models.BooleanField(default=True),
        ),
    ]
