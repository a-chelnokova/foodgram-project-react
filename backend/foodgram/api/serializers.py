import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import CustomUser, Subscription


class Base64ImageField(serializers.ImageField):
    """Сериализатор для создания кастомного типа поля для картинки"""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Укороченный сериализатор для модели Recipe."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = '__all__'


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации новых пользователей."""

    class Meta:
        model = CustomUser
        fields = '__all__'


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели CustomUser."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous or request is None:
            return False
        return Subscription.objects.filter(user=request.user,
                                           author=obj).exists()


class ShowSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок пользователя."""

    author_recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name',
                  'author_recipes', 'recipes_count', 'is_subscribed')

    def get_author_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj)
        return ShortRecipeSerializer(recipes, read_only=True, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Subscription.objects.filter(author=obj, user=user).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Subscription."""

    class Meta:
        model = Subscription
        fields = '__all__'

    def to_representation(self, instance):
        return ShowSubscriptionSerializer(instance.author, read_only=True,
                                          many=True).data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('name', 'color')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeIngredient."""

    ingredient = IngredientSerializer()
    measurement_unit = serializers.SerializerMethodField()

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount', 'measurement_unit')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""

    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()
    tags = TagSerializer(many=True)
    author = CustomUserSerializer()

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe

        fields = ('pub_date', 'name', 'ingredients', 'tags', 'text',
                  'cooking_time', 'image', 'author',
                  'is_favorited', 'is_in_shopping_cart')

        read_only_fields = ('author',)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context['request'].user

        recipe = Recipe.objects.create(**validated_data,
                                       author=author,
                                       tags=tags)

        for ingredient in ingredients:
            RecipeIngredient.objects.create(recipe=recipe,
                                            ingredient=ingredient,
                                            amount=ingredient.get('amount'))
        return recipe

    def update(self, instance, validated_data):
        instance.tags = validated_data.get('tags', instance.tags)

        if ingredients in validated_data:
            ingredients = validated_data.pop('ingredients')

            for ingredient in ingredients:
                RecipeIngredient.objects.update_or_create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=ingredient.get('amount')
                )
        return super().update(instance, validated_data)

    def get_is_favorited(self, obj):
        user = self.context['request'].user

        if user.is_anonymous:
            return False
        return Favorite.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user

        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(recipe=obj, user=user).exists()


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Favorite."""

    recipe = ShortRecipeSerializer()

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ShoppingCart."""

    recipe = ShortRecipeSerializer()

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
