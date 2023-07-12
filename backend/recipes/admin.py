from django.contrib.admin import ModelAdmin, register, StackedInline, display

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'color')


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class RecipeIngredientAdmin(StackedInline):
    model = RecipeIngredient
    autocomplete_fields = ('ingredient',)


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = (
        'id', 'get_author', 'name', 'text',
        'cooking_time', 'get_tags', 'get_ingredients',
        'pub_date', 'get_favorite_count'
    )
    search_fields = (
        'name', 'cooking_time',
        'author__email', 'ingredients__name'
    )
    list_filter = ('pub_date', 'tags',)
    inlines = (RecipeIngredientAdmin,)

    @display(description='В избранном')
    def get_favorite_count(self, obj):
        return obj.in_favourites.count()

    @display(
        description='Электронная почта автора')
    def get_author(self, obj):
        return obj.author.email

    @display(description='Теги')
    def get_tags(self, obj):
        list_ = [_.name for _ in obj.tags.all()]
        return ', '.join(list_)

    @display(description=' Ингредиенты ')
    def get_ingredients(self, obj):
        return '\n '.join([
            f'{item["ingredient__name"]} - {item["amount"]}'
            f' {item["ingredient__measurement_unit"]}.'
            for item in obj.values(
                'ingredient__name',
                'amount', 'ingredient__measurement_unit')])


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    pass


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    pass
