from datetime import datetime as dt

from api.mixins import AddDelViewMixin
from api.permissions import (AdminOrReadOnly, AuthorStaffOrReadOnly)
from core.enums import Tuples, UrlQueries
from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import F, Q, QuerySet, Sum
from django.http.response import HttpResponse
from djoser.views import UserViewSet as DjoserUserViewSet
from foodgram.settings import DATE_TIME_FORMAT
from recipes.models import Favorite, Ingredient, Recipe, ShoppingList, Tag
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from users.models import Subscription, User

from api.serializers import (GetObjectSerializer, IngredientsSerializer,
                             RecipesSerializer, TagSerializer,
                             UserSubscribeSerializer)

User = get_user_model()


class UserViewSet(DjoserUserViewSet, AddDelViewMixin):
    """ViewSet для работы с пользователми."""
    
    add_serializer = UserSubscribeSerializer
    permission_classes = (DjangoModelPermissions,)

    @action(
        methods=Tuples.ACTION_METHODS,
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request: WSGIRequest, id) -> Response:
        """Создаёт и удалет подписки пользователей."""
        return self._add_del_obj(id, Subscription, Q(author__id=id))

    @action(methods=('get',), detail=False)
    def subscriptions(self, request: WSGIRequest) -> Response:
        """Возвращает список подписок пользоваетеля."""
        if self.request.user.is_anonymous:
            return Response(status=HTTP_401_UNAUTHORIZED)

        pages = self.paginate_queryset(
            User.objects.filter(subscribers__user=self.request.user)
        )
        serializer = UserSubscribeSerializer(pages, many=True)
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для ингредиентов.
    Создавать новые ингредиенты и вносить изменения в существующие
    могут только администраторы.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    permission_classes = (AdminOrReadOnly,)


class RecipeViewSet(viewsets.ModelViewSet, AddDelViewMixin):
    """
    ViewSet для рецептов.
    Вносить изменения в рецепты или удалять их
    могут только авторы и администраторы.
    """

    queryset = Recipe.objects.select_related('author')
    serializer_class = RecipesSerializer
    add_serializer = GetObjectSerializer
    permission_classes = (AuthorStaffOrReadOnly,)

    def get_queryset(self) -> QuerySet[Recipe]:
        """Получает queryset в соответствии с параметрами запроса."""
        queryset = self.queryset

        tags: list = self.request.query_params.getlist(UrlQueries.TAGS.value)
        if tags:
            queryset = queryset.filter(
                tags__slug__in=tags).distinct()

        author: str = self.request.query_params.get(UrlQueries.AUTHOR.value)
        if author:
            queryset = queryset.filter(author=author)

        if self.request.user.is_anonymous:
            return queryset

        is_in_cart: str = self.request.query_params.get(UrlQueries.SHOP_CART)
        if is_in_cart in Tuples.SYMBOL_TRUE_SEARCH.value:
            queryset = queryset.filter(in_carts__user=self.request.user)
        elif is_in_cart in Tuples.SYMBOL_FALSE_SEARCH.value:
            queryset = queryset.exclude(in_carts__user=self.request.user)

        is_favorite: str = self.request.query_params.get(UrlQueries.FAVORITE)
        if is_favorite in Tuples.SYMBOL_TRUE_SEARCH.value:
            queryset = queryset.filter(in_favorites__user=self.request.user)
        if is_favorite in Tuples.SYMBOL_FALSE_SEARCH.value:
            queryset = queryset.exclude(in_favorites__user=self.request.user)

        return queryset

    @action(
        methods=Tuples.ACTION_METHODS,
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request: WSGIRequest, pk) -> Response:
        """Добавляет рецепт в избранное и удаляет его оттуда."""
        return self._add_del_obj(pk, Favorite, Q(recipe__id=pk))

    @action(
        methods=Tuples.ACTION_METHODS,
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_list(self, request: WSGIRequest, pk) -> Response:
        """Добавляет рецепт в список покупок и удаляет его оттуда."""
        return self._add_del_obj(pk, ShoppingList, Q(recipe__id=pk))

    @action(methods=('get',), detail=False)
    def download_shopping_list(self, request: WSGIRequest) -> Response:
        """
        Возвращает текстовый файл (.txt) со списком ингредиентов.
        Считает сумму ингредиентов в рецептах, выбранных для покупки.
        """
        user = self.request.user
        if not user.shopping_list.exists():
            return Response(status=HTTP_400_BAD_REQUEST)

        filename = f'{user.username}_shopping_list.txt'
        shopping_list = [
            f'Список покупок для:\n\n{user.first_name}\n'
            f'{dt.now().strftime(DATE_TIME_FORMAT)}\n'
        ]

        ingredients = Ingredient.objects.filter(
            recipe__recipe__in_shopping_list__user=user
        ).values(
            'name',
            measurement=F('measurement_unit')
        ).annotate(amount=Sum('recipe__amount'))

        for ing in ingredients:
            shopping_list.append(
                f'{ing["name"]}: {ing["amount"]} {ing["measurement"]}'
            )

        shopping_list.append('\nПосчитано в Foodgram')
        shopping_list = '\n'.join(shopping_list)
        response = HttpResponse(
            shopping_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
