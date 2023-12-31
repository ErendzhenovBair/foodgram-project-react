# Generated by Django 3.2.15 on 2023-09-14 15:15

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_auto_20230909_2316'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(max_length=200, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='ingredientsamount',
            name='amount',
            field=models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1, 'the weight cannot be less than 1')], verbose_name='quantity'),
        ),
    ]
