# Generated by Django 3.2.15 on 2023-09-21 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0015_auto_20230921_2228'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='IngredientsAmount',
            new_name='IngredientAmount',
        ),
        migrations.AlterModelOptions(
            name='ingredientamount',
            options={'verbose_name': 'Ingredient amount'},
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(db_index=True, max_length=200, verbose_name='Ingredient Name'),
        ),
    ]
