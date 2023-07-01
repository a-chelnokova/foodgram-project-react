from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet
from users.views import (SubscriptionListViewSet,
                         SubscriptionViewSet, AuthToken)

app_name = 'api'

router = DefaultRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')


urlpatterns = [
    path('auth/token/login/', AuthToken.as_view(), name='login'),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('users/subscriptions', SubscriptionListViewSet.as_view(),
         name='users/subscriptions'),
    path('users/<int:id>/subscribe/', SubscriptionViewSet.as_view(),
         name='subscribe'),
    path('auth/', include('djoser.urls.authtoken')),
]
