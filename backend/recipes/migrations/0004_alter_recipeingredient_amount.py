# Generated by Django 3.2.13 on 2023-07-13 11:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20230712_1441'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.CharField(max_length=4, verbose_name='Количество ингредиента'),
        ),
    ]
