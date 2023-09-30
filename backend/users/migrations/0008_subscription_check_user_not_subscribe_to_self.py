# Generated by Django 3.2.15 on 2023-09-29 23:58

from django.db import migrations, models
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_remove_subscription_check_user_not_subscribe_to_self'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='subscription',
            constraint=models.CheckConstraint(check=models.Q(('user', django.db.models.expressions.F('author')), _negated=True), name='check_user_not_subscribe_to_self'),
        ),
    ]