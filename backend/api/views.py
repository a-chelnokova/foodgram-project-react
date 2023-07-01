from django.db.models import Sum
from django.http import HttpResponse
#  from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from api.filters import IngredientFilter, RecipeFilter
#  from api.pagination import CustomPagination
from api.permissions import AuthorOrReadOnly
from api.serializers import (IngredientSerializer,
                             RecipeSerializer, ShortRecipeSerializer,
                             TagSerializer, CreateRecipeSerializer,
                             FavoriteSerializer, ShoppingCartSerializer)
#  from api.utils import PostDeleteMixin
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class IngredientViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет для модели Ingredient."""

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

    pagination_class = None
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrReadOnly, )
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return RecipeSerializer
        return CreateRecipeSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(author=user)
        return serializer

    def get_queryset(self):
        queryset = Recipe.objects.all()
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        favorite = Favorite.objects.filter(user=self.request.user.id)
        shopping_cart = ShoppingCart.objects.filter(user=self.request.user.id)
        if is_favorited == 'true':
            queryset = queryset.filter(favorites__in=favorite)
        elif is_favorited == 'false':
            queryset = queryset.exclude(favorites__in=favorite)
        if is_in_shopping_cart == 'true':
            queryset = queryset.filter(shopping__in=shopping_cart)
        elif is_in_shopping_cart == 'false':
            queryset = queryset.exclude(shopping__in=shopping_cart)
        return queryset

    @action(detail=True,
            methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated, ),
            pagination_class=None,)
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = FavoriteSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        if request.method == 'GET':
            serializer.is_valid(raise_exception=True)
            serializer.save(recipe=recipe, user=request.user)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        favorite = get_object_or_404(
            Favorite, recipe=recipe, user=request.user
        )
        self.perform_destroy(favorite)
        return Response(
            f'Рецепт {recipe} удален из избранного.',
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True,
            methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated,),
            pagination_class=None,)
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = ShoppingCartSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        if request.method == 'GET':
            serializer.is_valid(raise_exception=True)
            serializer.save(recipe=recipe, user=request.user)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        shopping_cart = get_object_or_404(
            ShoppingCart, recipe=recipe, user=request.user
        )
        self.perform_destroy(shopping_cart)
        return Response(
            f'Рецепт {recipe} удален из списка покупок.',
            status=status.HTTP_204_NO_CONTENT
        )

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
