from django_filters import rest_framework as filter
from rest_framework.filters import SearchFilter
from recipes.models import Recipe, Tag
from users.models import CustomUser


class IngredientFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(filter.FilterSet):
    author = filter.ModelChoiceFilter(queryset=CustomUser.objects.all())
    tags = filter.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        label='Tags',
        to_field_name='slug',
    )

    is_favorited = filter.NumberFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filter.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorite_recipes__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(shopping_recipes__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = [
            'tags',
            'author',
            'in_favorites',
            'is_in_shopping_cart'
        ]
