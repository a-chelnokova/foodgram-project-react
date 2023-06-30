from rest_framework import serializers

from api.fields import Base64ImageField
from api.utils import UserCreateMixin
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

    author_recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name',
                  'author_recipes', 'recipes_count', 'is_subscribed')

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


class RecipeTagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeTag."""

    

class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""

    ingredients = RecipeIngredientSerializer(many=True)
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe

        fields = ('pub_date', 'name', 'ingredients', 'tags', 'text',
                  'cooking_time', 'image', 'author',
                  'is_favorited', 'is_in_shopping_cart')

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


class CreateRecipeSerializer(serializers.ModelSerializer):

    ingredients = RecipeIngredientSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('name', 'tags', 'ingredients', 'cooking_time',
                  'text','image', 'author')

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
                                       author=author)

        RecipeIngredient.objects.bulk_create([RecipeIngredient(
            ingredient=ingredient['ingredient'],
            recipe=recipe,
            amount=ingredient['amount'])
            for ingredient in ingredients])

        for tag in tags:
            RecipeTag.objects.create(recipe=recipe, tag=tag)

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
