# Generated by Django 3.2.15 on 2023-09-26 08:28

from django.db import migrations, models
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_subscription_check_user_not_subscribe_to_self'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='subscription',
            name='check_user_not_subscribe_to_self',
        ),
        migrations.AddConstraint(
            model_name='subscription',
            constraint=models.CheckConstraint(check=models.Q(('user', django.db.models.expressions.F('author'))), name='check_user_not_subscribe_to_self'),
        ),
    ]
