from django.contrib.admin import ModelAdmin, register

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'color')


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


@register(RecipeIngredient)
class RecipeIngredientAdmin(ModelAdmin):
    pass


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('author', 'name', 'tags')

    def in_favorite_count(self, obj):
        return obj.in_favourites.count()


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    pass


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    pass
