from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.db import transaction

from recipes.models import Favorite, Recipe
from users.models import CustomUser, Subscription


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для регистрации новых пользователей."""

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password')

    @transaction.atomic
    def create(self, validated_data):
        user = super(CustomUserCreateSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class CustomUserSerializer(UserSerializer):
    """Сериализатор для модели CustomUser."""

    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed'
    )

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user,
            author=obj,
        ).exists()


class RecipeFollowSerializer(serializers.ModelSerializer):
    """Сериализатор для получение информации о рецепте."""

    def is_favorite_user(self, user):
        return Favorite.objects.filter(
            user=user, recipe=self.instance).exists()

    def add_favorite_user(self, user):
        favorite, created = Favorite.objects.get_or_create(
            user=user, recipe=self.instance)
        if not created:
            raise serializers.ValidationError('Рецепт уже в избранном')

    def remove_favorite_user(self, user):
        favorite = Favorite.objects.filter(user=user, recipe=self.instance)
        if favorite:
            favorite.delete()
        else:
            raise serializers.ValidationError('Рецепта нет в избранном')

    def validate(self, data):
        user = self.context['request'].user
        if self.context['request'].method == 'POST' and \
                self.is_favorite_user(user):
            raise serializers.ValidationError('Рецепт уже в избранном')
        if self.context['request'].method == 'DELETE' and \
                not self.is_favorite_user(user):
            raise serializers.ValidationError('Рецепта нет в избранном')
        return data

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок пользователя."""

    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    email = serializers.ReadOnlyField(source='author.email')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes_count = serializers.ReadOnlyField(source='author.recipes.count')

    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed'
    )
    recipes = serializers.SerializerMethodField(method_name='get_recipes')

    class Meta:
        model = Subscription
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'recipes',
            'recipes_count',
            'is_subscribed',
        ]

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            user=obj.user,
            author=obj.author
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[:int(limit)]
        return RecipeFollowSerializer(queryset, many=True).data
