from rest_framework import serializers
from django.shortcuts import get_object_or_404
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

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = [
            'id',
            'amount',
            'recipe',
        ]


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


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""

    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()

    ingredients = serializers.SerializerMethodField(
        method_name='get_ingredients'
    )
    in_favorites = serializers.SerializerMethodField(
        method_name='get_in_favorites'
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

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data


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

    def validate_ingredients(self, data):
        if len(data['tags']) == 0:
            raise serializers.ValidationError('Укажите хотя бы один тег.')

        if len(set(data['tags'])) != len(data['tags']):
            raise serializers.ValidationError('Теги не должны повторяться.')

        if data.get('cooking_time', 0) < 1:
            raise serializers.ValidationError(
                'Минимальное время приготовления 1 минута.')

        if len(data['ingredients']) < 1:
            raise serializers.ValidationError(
                'Укажите хотя бы один ингредиент.')
        ingredients_id = set()
        for ingredient in data['ingredients']:
            if ingredient['id'] in ingredients_id:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.')
            ingredients_id.add(ingredient['id'])

        return data

    def create_ings(self, ingredients, recipe):
        ings_list = []

        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient_fr = get_object_or_404(
                Ingredient,
                pk=ingredient['id']
            ),
            ingredient_obj = RecipeIngredient(
                recipe=recipe,
                amount=amount,
                ingredient=ingredient_fr,
            )
            ings_list.append(ingredient_obj)

        RecipeIngredient.objects.bulk_create(ings_list)

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

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get(
            'text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if ingredients:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self.create_ings(ingredients, recipe=instance)

        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализтор для списка избранного."""
    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe',)
