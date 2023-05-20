from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (FavoriteView, IngredientViewSet, RecipeViewSet,
                       ShoppingListView, ShowSubscriptionsView, SubscribeView,
                       TagViewSet, download_shopping_list)

app_name = 'api'

router = DefaultRouter()

router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path(
        'recipes/download_shopping_list/',
        download_shopping_list,
        name='download_shopping_list'
    ),
    path(
        'recipes/<int:id>/shopping_cart/',
        ShoppingListView.as_view(),
        name='shopping_cart'
    ),
    path(
        'recipes/<int:id>/favorite/',
        FavoriteView.as_view(),
        name='favorite'
    ),
    path(
        'users/<int:id>/subscribe/',
        SubscribeView.as_view(),
        name='subscribe'
    ),
    path(
        'users/subscriptions/',
        ShowSubscriptionsView.as_view(),
        name='subscriptions'
    ),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
    path('', include(router.urls)),
    ]
