from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import filters

from api.pagination import CustomPagination
from api.serializers import (IngredientSerializer,
                             RecipeSerializer,
                             TagSerializer, CreateRecipeSerializer,
                             ShortRecipeSerializer)
from api.utils import PostDeleteMixin
from api.permissions import AuthorOrAdminOrReadOnly
from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag, Favorite)
from api.filters import IngredientFilter, RecipeFilter


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели Ingredient."""

    queryset = Ingredient.objects.all()
    permission_classes = [AllowAny, ]
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter
    search_fields = ['^name', ]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели Tag."""

    permission_classes = [AllowAny, ]
    pagination_class = None
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class RecipeViewSet(
    viewsets.ModelViewSet,
    PostDeleteMixin
):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrAdminOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH', 'DELETE'):
            return CreateRecipeSerializer
        return RecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        self.perform_destroy(self.get_object())
        return Response(
            {'massage': 'Рецепт успешно удален'},
            status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['POST', 'DELETE'])
    def favorite(self, request, pk=None):
        return self.post_delete(Favorite, ShortRecipeSerializer,
                                request, pk)

    @action(
        methods=['GET'],
        detail=False,)
    def favorites(self, request):
        """
        Возвращает список пользователей, на которых
        подписан текущий пользователь.
        """
        user = request.user
        queryset = Favorite.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = ShortRecipeSerializer(
            pages,
            many=True,
            context={'request': request}
        )

        response_data = {
            'count': len(pages),
            'next': self.paginator.get_next_link(),
            'previous': self.paginator.get_previous_link(),
            'results': serializer.data}
        return Response(response_data)

    @action(detail=True,
            methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk=None):
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
