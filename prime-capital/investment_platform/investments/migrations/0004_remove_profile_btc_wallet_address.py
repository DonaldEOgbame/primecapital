# Generated by Django 5.0.2 on 2024-03-01 11:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('investments', '0003_transaction_withdrawal_request_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='btc_wallet_address',
        ),
    ]
