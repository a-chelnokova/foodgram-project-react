from rest_framework import serializers
from django.db import transaction

from api.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.serializers import CustomUserSerializer


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Укороченный сериализатор для модели Recipe."""

    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'image',
            'cooking_time',
        ]


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = [
            'id',
            'name',
            'measurement_unit',
        ]


class AddIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиента в рецепт."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ShoppingCart."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeIngredient."""
    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


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

    def validate_ingredients(self, ingredients):
        ing_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ing_ids) != len(set(ing_ids)):
            raise serializers.ValidationError(
                'Нельзя дублировать ингредиенты.'
            )
        return ingredients

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(**validated_data,
                                       author=author,
                                       tags=tags)
        RecipeIngredient.objects.bulk_create([RecipeIngredient(
            ingredient=ingredient['ingredient'],
            recipe=recipe,
            amount=ingredient['amount'])
            for ingredient in ingredients])
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

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализтор для списка избранного."""
    id = serializers.IntegerField(source='recipe.id')
    name = serializers.CharField(source='recipe.name')
    image = Base64ImageField(source='recipe.image')
    cooking_time = serializers.IntegerField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')
