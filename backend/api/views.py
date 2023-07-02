from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.serializers import (IngredientSerializer,
                             RecipeSerializer, FavoriteSerializer,
                             TagSerializer, CreateRecipeSerializer)
from api.utils import PostDeleteMixin, shopcart_or_favorite
from api.permissions import AuthorOrAdminOrReadOnly
from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag, Favorite)
from users.serializers import RecipeFollowSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Ingredient."""

    queryset = Ingredient.objects.all()
    permission_classes = [AllowAny, ]
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = IngredientFilter
    search_fields = ['^name', ]
    pagination_class = None


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Tag."""

    queryset = Tag.objects.all()
    permission_classes = [AllowAny, ]
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(
    PostDeleteMixin,
    viewsets.ModelViewSet
):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrAdminOrReadOnly,)
    pagination_class = CustomPagination
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend, ]
    filter_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH', 'DELETE'):
            return CreateRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(author=user)

    def destroy(self, request, *args, **kwargs):
        self.perform_destroy(self.get_object())
        return Response(
            {'massage': 'Рецепт успешно удален'},
            status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, ],
        url_name='favorite',
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        return shopcart_or_favorite(
            self,
            request,
            Favorite,
            FavoriteSerializer,
            pk,
        )

    @action(detail=True,
            methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk=None):
        return self.post_delete(ShoppingCart, RecipeFollowSerializer,
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
