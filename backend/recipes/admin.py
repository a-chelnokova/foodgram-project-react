from django.contrib.admin import ModelAdmin, StackedInline, register
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'color']


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ['name', 'measurement_unit']
    search_fields = ['name']


class IngredientsInLine(StackedInline):
    model = RecipeIngredient
    autocomplete_fields = ['ingredient', ]


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ['id', 'name', 'author', 'is_favorited_count']
    list_filter = ['tags']
    search_fields = ['name', 'author__username']
    inlines = (IngredientsInLine, )

    def is_favorited_count(self, obj):
        return obj.is_favorited.count()


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    pass


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    pass
