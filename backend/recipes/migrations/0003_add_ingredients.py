from django.db import migrations, IntegrityError, transaction

import json


def make_ings_dict(ingredient):
    fields = {
        'name': None,
        'measurement_unit': None
    }

    for key, value in ingredient.items():
        fields[key] = value
    return fields


def add_ings(apps, schema_editor):
    Ingredient = apps.get_model('recipes', 'Ingredient')
    db_alias = schema_editor.connection.alias

    with open('ingredients.json', encoding='utf-8') as file:
        ingredients = json.load(file)
        for ingredient in ingredients:
            try:
                fields = make_ings_dict(ingredient)

                with transaction.atomic():
                    Ingredient.objects.using(db_alias).create(
                        name=fields['name'],
                        measurement_unit=fields['measurement_unit']
                    )
            except IntegrityError:
                continue


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(add_ings),
    ]
