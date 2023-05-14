"""Валидаторы."""
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from recipes.models import Ingredient, Tag

def tags_exist_validator(tags_ids: list[int, str], Tag: 'Tag') -> None:
    """Проверяет наличие тегов с указанными id."""
    exists_tags = Tag.objects.filter(id__in=tags_ids)

    if len(exists_tags) != len(tags_ids):
        raise ValidationError('Такого тега не существует')

def ingredients_validator(ingredients: list[dict[str, str, int]],
                          Ingredient: 'Ingredient',
                          ) -> dict[int, tuple['Ingredient', int]]:
    """Проверяет список ингридиентов."""
    valid_ingredients = {}

    for ingredient in ingredients:
        if not (isinstance(ingredient['amount'], int)
                or ingredient['amount'].isdigit()):
            raise ValidationError('Неправильное количество ингидиента')

        amount = valid_ingredients.get(
            ingredient['id'], 0) + int(ingredient['amount'])
        if amount <= 0:
            raise ValidationError('Неправильное количество ингридиента')

        valid_ingredients[ingredient['id']] = amount

    if not valid_ingredients:
        raise ValidationError('Неправильные ингидиенты')

    db_ingredients = Ingredient.objects.filter(pk__in=valid_ingredients.keys())
    if not db_ingredients:
        raise ValidationError('Неправильные ингидиенты')

    for ingredient in db_ingredients:
        valid_ingredients[ingredient.pk] = (ingredient,
                                            valid_ingredients[ingredient.pk])

    return valid_ingredients
