from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
#  from api.permissions import AuthorOrReadOnly
from api.serializers import (IngredientSerializer,
                             RecipeSerializer, ShortRecipeSerializer,
                             TagSerializer, CreateRecipeSerializer)
from api.utils import PostDeleteMixin
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class IngredientViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет для модели Ingredient."""

    permission_classes = [AllowAny, ]
    pagination_class = None
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filterset_class = IngredientFilter
    search_fields = ['^name', ]


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет для модели Tag."""

    permission_classes = [AllowAny, ]
    pagination_class = None
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class RecipeViewSet(
    PostDeleteMixin,
    viewsets.ModelViewSet
):
    """Вьюсет для модели Recipe."""

    permission_classes = [AllowAny, ]
    pagination_class = CustomPagination
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return CreateRecipeSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(author=user)

    @action(detail=True,
            methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk=None):
        return self.post_delete(Favorite, ShortRecipeSerializer,
                                request, pk)

    @action(detail=True,
            methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        return self.post_delete(ShoppingCart, ShortRecipeSerializer,
                                request, pk)

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        shopping_ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values("ingredient__name", "ingredient__measurement_unit"
                 ).annotate(amount=Sum('amount_sum'))

        shopping_cart = '\n'.join([
            f'{ingredient["ingredients__name"]} - {ingredient["amount_sum"]}'
            f'{ingredient["ingredients__measurement_unit"]}'
            for ingredient in shopping_ingredients
        ])

        response = HttpResponse(shopping_cart, content_type='text/plain')
        response['Content-Disposition'] = ('attachment; '
                                           'filename="shopping_cart.txt"')
        return response

    def add_recipe(self, model, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        if model.objects.filter(recipe=recipe, user=user).exists():
            raise ValidationError('Рецепт уже добавлен')
        model.objects.create(recipe=recipe, user=user)
        serializer = ShortRecipeSerializer(recipe)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe(self, model, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        obj = get_object_or_404(model, recipe=recipe, user=user)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
