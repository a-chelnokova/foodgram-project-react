from rest_framework import serializers
from django.shortcuts import get_object_or_404

from api.fields import Base64ImageField
from api.utils import UserCreateMixin, PostDeleteMixin
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag, RecipeTag)
from users.models import CustomUser, Subscription


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Укороченный сериализатор для модели Recipe."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = '__all__'


class CustomUserCreateSerializer(UserCreateMixin,
                                 serializers.ModelSerializer):
    """Сериализатор для регистрации новых пользователей."""

    class Meta:
        model = CustomUser
        fields = fields = [
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        ]


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели CustomUser."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous or request is None:
            return False
        return Subscription.objects.filter(user=request.user,
                                           author=obj).exists()


class ShowSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок пользователя."""

    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous or request is None:
            return False
        return Subscription.objects.filter(author=obj,
                                           user=request.user).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous or request is None:
            return False
        recipes = Recipe.objects.filter(author=obj)
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return ShortRecipeSerializer(recipes, many=True,
                                     context={'request': request}).data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Subscription."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def to_representation(self, instance):
        return ShowSubscriptionSerializer(instance.author,
                                          context={'request':
                                                   self.context.get('request')
                                                   }).data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = ('id', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeIngredient."""

    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(PostDeleteMixin,
                       serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""

    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)

    ingredients = serializers.SerializerMethodField()
    in_favorites = serializers.SerializerMethodField()
    in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe

        fields = ('id', 'tags', 'author', 'ingredients',
                  'in_favorites', 'in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_in_favorites(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()

    def get_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe_id=obj).exists()


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования рецептов."""

    ingredients = RecipeIngredientSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('name', 'tags', 'ingredients', 'cooking_time',
                  'text', 'image', 'author')

    def validate_ingredients(self, ingredients):
        ing_ids = [ingredient['id'] for ingredient in ingredients]

        if len(ing_ids) != len(set(ing_ids)):
            raise serializers.ValidationError(
                'Нельзя дублировать ингредиенты.'
            )
        return ingredients

    def create(self, validated_data):
        # ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user

        recipe = Recipe.objects.create(**validated_data,
                                       author=author)

        # for ingredient in ingredients:
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=Ingredient.objects.get(name='пагр'),
            amount='12',
        )

        for tag in tags:
            RecipeTag.objects.create(recipe=recipe, tags=tag)

        return recipe

    def update(self, instance, validated_data):
        instance.tags = validated_data.get('tags', instance.tags)
        ingredients = validated_data.pop('ingredients')

        if ingredients in validated_data:

            for ingredient in ingredients:
                RecipeIngredient.objects.update_or_create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=ingredient.get('amount')
                )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')}).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Favorite."""

    recipe = ShortRecipeSerializer()

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ShoppingCart."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.HiddenField(default=None)

    def validate_recipe(self, value):
        recipe_id = self.context['request'].parser_context['kwargs']['pk']
        return get_object_or_404(Recipe, pk=recipe_id)

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
