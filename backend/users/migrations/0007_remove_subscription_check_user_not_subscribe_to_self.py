# Generated by Django 3.2.15 on 2023-09-29 21:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_subscription_options'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='subscription',
            name='check_user_not_subscribe_to_self',
        ),
    ]
