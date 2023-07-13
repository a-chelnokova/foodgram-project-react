from django_filters import rest_framework as filter
from django_filters.rest_framework import FilterSet
import django_filters as filters
from recipes.models import Recipe, Tag, Ingredient, Favorite
from users.models import CustomUser


class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filter.FilterSet):
    author = filter.ModelChoiceFilter(queryset=CustomUser.objects.all())
    tags = filter.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        label='Tags',
        to_field_name='slug',
    )

    is_favorited = filters.BooleanFilter(
        field_name='is_favorited', method='filter'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        widget=filters.widgets.BooleanWidget(),
        label='В корзине.')

    def filter(self, queryset, name, value):
        if name == 'is_in_shopping_cart' and value:
            queryset = queryset.filter(
                shopping_cart__user=self.request.user
            )
        if name == 'is_favorited' and value:
            queryset = Recipe.objects.filter(
                favorites__user=self.request.user
            )
        return queryset

    """def filter_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorite_recipes__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(shopping_recipes__user=self.request.user)
        return queryset"""

    class Meta:
        model = Recipe
        fields = [
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        ]
