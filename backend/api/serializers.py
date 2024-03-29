from rest_framework import serializers

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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeIngredient."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = [
            'id',
            'name',
            'measurement_unit',
            'amount',
        ]


class AddIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиента в рецепт."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(write_only=True, min_value=1)
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = [
            'id',
            'amount',
            'recipe',
        ]


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""

    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(
        many=True,
        read_only=True,
        source='recipeingredient_set',
    )

    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

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
            'is_favorited',
            'is_in_shopping_cart',
            'cooking_time',
        ]

    def in_list_exists(self, obj, model):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return model.objects.filter(
            user=user,
            recipe=obj,
        ).exists()

    def get_is_favorited(self, obj):
        return self.in_list_exists(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.in_list_exists(obj, ShoppingCart)


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования рецептов."""

    ingredients = AddIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'author',
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
        RecipeIngredient.objects.bulk_create([RecipeIngredient(
            ingredient_id=ingredient['id'],
            recipe=recipe,
            amount=ingredient['amount'])
            for ingredient in ingredients])

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)

        for tag in tags:
            recipe.tags.add(tag)

        self.create_ings(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self.create_ings(ingredients, recipe=instance)

        return super().update(instance, validated_data)
