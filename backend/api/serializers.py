from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db import transaction

from api.fields import Base64ImageField
from api.utils import UserCreateMixin
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import CustomUser, Subscription


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


class CustomUserCreateSerializer(UserCreateMixin,
                                 serializers.ModelSerializer):
    """Сериализатор для регистрации новых пользователей."""

    class Meta:
        model = CustomUser
        fields = [
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        ]


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели CustomUser."""

    is_subscribed = serializers.SerializerMethodField()

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
        if request.user.is_anonymous or request is None:
            return False
        return Subscription.objects.filter(
            user=request.user,
            author=obj,
        ).exists()


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
        fields = '__all__'


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

    class Meta:
        model = RecipeIngredient
        fields = [
            'id',
            'amount',
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


class ShowSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок пользователя."""

    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

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

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous or request is None:
            return False
        return Subscription.objects.filter(
            author=obj.author,
            user=request.user
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request.GET.get('recipe_limit'):
            recipe_limit = int(request.GET.get('recipe_limit'))
            queryset = Recipe.objects.filter(
                author=obj.author)[:recipe_limit]
        else:
            queryset = Recipe.objects.filter(
                author=obj.author)
        serializer = ShortRecipeSerializer(
            queryset, read_only=True, many=True
        )
        return serializer.data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Subscription."""

    class Meta:
        model = Subscription
        fields = [
            'user',
            'author',
        ]

    def to_representation(self, instance):
        return ShowSubscriptionSerializer(instance,
                                          context={'request':
                                                   self.context.get('request')
                                                   }).data

    def validate(self, data):
        author = data.get('author')
        user = data.get('user')

        if author == user:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя'
            )
        return data


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
    """Сериализатор для создания и редактирования рецептов."""

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
