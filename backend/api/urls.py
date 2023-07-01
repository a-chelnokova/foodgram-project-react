from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet
from users.views import UsersViewSet

app_name = 'api'

router = DefaultRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users', UsersViewSet, basename='users')


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

"""
path('users/subscriptions', SubscriptionListViewSet.as_view(),
         name='users/subscriptions'),
    path('users/<int:id>/subscribe/', SubscriptionViewSet.as_view(),
         name='subscribe'),
"""
