from collections import OrderedDict

from core.services import recipe_ingredients_set
from core.validators import ingredients_validator, tags_exist_validator
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import F, QuerySet
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, Tag
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from django.db.transaction import atomic

User = get_user_model()


class GetObjectSerializer(serializers.ModelSerializer):
    """Укороченный сериализатор для модели Recipe."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = '__all__'


class UserSerializer(ModelSerializer):
    """Сериализатор для модели User."""

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = 'is_subscribed',

    def get_is_subscribed(self, obj: User) -> bool:
        """
        Проверка, подписан ли текущий пользователь
        на просматриваемого пользователя.
        """
        user = self.context.get('request').user

        if user.is_anonymous or (user == obj):
            return False

        return user.subscriptions.filter(author=obj).exists()

    def create(self, validated_data: dict) -> User:
        """Создание нового пользователя."""
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserSubscribeSerializer(UserSerializer):
    """
    Сериализатор для вывода авторов,
    на которых подписан текущий пользователь.
    """

    recipes = GetObjectSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = '__all__',

    def get_is_subscribed(*args) -> bool:
        """Проверка подписки пользователей."""
        return True

    def get_recipes_count(self, obj: User) -> int:
        """Показывает общее количество рецептов у каждого автора."""
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__'


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__'


class RecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""

    image = Base64ImageField()
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)

    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_list = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_list',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        read_only_fields = (
            'is_favorite',
            'is_shopping_cart',
        )

    def get_ingredients(self, recipe: Recipe) -> QuerySet[dict]:
        """Получает список ингредиентов для рецепта."""
        ingredients = recipe.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F('recipe__amount')
        )
        return ingredients

    def get_is_favorited(self, recipe: Recipe) -> bool:
        """Проверяет, находится ли рецепт в избранном."""
        user = self.context.get('view').request.user

        if user.is_anonymous:
            return False

        return user.favorites.filter(recipe=recipe).exists()

    def get_is_in_shopping_list(self, recipe: Recipe) -> bool:
        """Проверяет, находится ли рецепт в списке покупок."""
        user = self.context.get('view').request.user

        if user.is_anonymous:
            return False

        return user.shopping_list.filter(recipe=recipe).exists()

    def validate(self, data: OrderedDict) -> OrderedDict:
        """Проверяет данные при создании и редактировании рецепта."""
        tags_ids: list[int] = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')

        if not tags_ids or not ingredients:
            raise ValidationError('Недостаточно данных.')

        tags_exist_validator(tags_ids, Tag)
        ingredients = ingredients_validator(ingredients, Ingredient)

        data.update({
            'tags': tags_ids,
            'ingredients': ingredients,
            'author': self.context.get('request').user
        })
        return data

    @atomic
    def create(self, validated_data: dict) -> Recipe:
        """Создаёт новый рецепт."""
        tags: list[int] = validated_data.pop('tags')
        ingredients: dict[int, tuple] = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        recipe_ingredients_set(recipe, ingredients)
        return recipe

    @atomic
    def update(self, recipe: Recipe, validated_data: dict):
        """Обновляет существующий рецепт."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        for key, value in validated_data.items():
            if hasattr(recipe, key):
                setattr(recipe, key, value)

        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)

        if ingredients:
            recipe.ingredients.clear()
            recipe_ingredients_set(recipe, ingredients)

        recipe.save()
        return recipe
