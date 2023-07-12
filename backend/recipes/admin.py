from django.contrib.admin import ModelAdmin, register, StackedInline

from recipes.models import (Favorite, Ingredient, Recipe,
                            ShoppingCart, Tag, RecipeIngredient)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'color')


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class IngredientsInLine(StackedInline):
    model = RecipeIngredient
    autocomplete_fields = ('ingredient',)

@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorites')
    list_filter = ('tags')
    search_fields = ('name', 'author__username')
    inlines = (IngredientsInLine, )

    def in_favorite_count(self, obj):
        return obj.in_favourites.count()


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    pass


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    pass
