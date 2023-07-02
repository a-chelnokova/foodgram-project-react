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
        fields = [
            'id',
            'name',
            'color',
            'slug',
        ]

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

    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(
        source='ingredient_in_recipe',
        read_only=True,
        many=True,
    )

    in_favorites = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'name',
            'author',
            'ingredients',
            'image',
            'text',
            'in_favorites',
            'is_in_shopping_cart',
            'cooking_time',
        ]

    def in_list_exists(self, obj, model):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return model.objects.filter(
            user=request.user,
            recipe=obj,
        ).exists()

    def get_in_favorites(self, obj):
        return self.in_list_exists(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.in_list_exists(obj, ShoppingCart)


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/изменения рецепта."""

    ingredients = AddIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField(max_length=None)

    class Meta:
        model = Recipe
        fields = [
            'name',
            'tags',
            'ingredients',
            'cooking_time',
            'text',
            'image',
        ]

    def validate_ingredients(self, ingredients):
        ing_ids = [ingredient['id'] for ingredient in ingredients]

        if len(ing_ids) != len(set(ing_ids)):
            raise serializers.ValidationError(
                'Нельзя дублировать ингредиенты.'
            )
        return ingredients

    def create_ings(self, ingredients, recipe):
        ings_list = []

        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient_id = ingredient['id']
            ingredient_obj = RecipeIngredient(
                recipe=recipe,
                amount=amount,
                ingredient_id=ingredient_id,
            )
            ings_list.append(ingredient_obj)

        RecipeIngredient.objects.bulk_create(
            ings_list,
            ignore_conflicts=True,
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        recipe.save()
        self.create_ings(ingredients, recipe)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        instance.tags.clear()
        instance.tags.set(tags)

        instance.ingredients.clear()
        self.create_ings(ingredients, instance)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(instance).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализтор для списка избранного."""
    id = serializers.IntegerField(source='recipe.id')
    name = serializers.CharField(source='recipe.name')
    image = Base64ImageField(source='recipe.image')
    cooking_time = serializers.IntegerField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')
