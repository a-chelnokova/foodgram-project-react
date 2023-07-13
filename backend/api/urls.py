from django.urls import include, path
from rest_framework.routers import DefaultRouter
from django.contrib.auth.views import (PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet
from users.views import SubscribeView

app_name = 'api'

router = DefaultRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register(
    'users',
    SubscribeView,
    basename='users'
)

urlpatterns = [

    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path(
        'auth/password_reset/',
        PasswordResetView.as_view(),
        name='password_reset_form'
    ),
    path(
        'auth/password_reset/done/',
        PasswordResetDoneView.as_view(),
        name='password_reset_done'
    ),
    path(
        'auth/reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    path(
        'auth/reset/done/',
        PasswordResetCompleteView.as_view(),
        name='password_reset_complete'
    )
]
