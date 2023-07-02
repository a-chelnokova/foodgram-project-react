from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredient, Recipe, Tag
from users.models import CustomUser


class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    author = filters.ModelChoiceFilter(queryset=CustomUser.objects.all())
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__id',
        queryset=Tag.objects.all(),
        to_field_name='id',
    )

    is_favorited = filters.NumberFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorite_user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(shoppingcart_user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = [
            'tags',
            'author',
            'in_favorites',
            'is_in_shopping_cart'
        ]
