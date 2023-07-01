from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from users.models import CustomUser, Subscription
from recipes.models import Recipe
from api.serializers import ShortRecipeSerializer


class UserRegistrationSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return Subscription.objects.filter(
            user=request.user,
            author=obj
        ).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    author = serializers.SlugRelatedField(
        required=True,
        slug_field='username',
        queryset=CustomUser.objects.all()
    )

    class Meta:
        model = Subscription
        fields = ('user', 'author',)
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author'],
                message='Нельзя дважды подписаться на одного и того же автора.'
            )
        ]


class SubscriptionUserSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(default=True)

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes_count(self, obj):
        recipes = Recipe.objects.filter(author=obj)
        return recipes.count()

    def get_recipes(self, obj):
        queryset = obj.recipes.all()
        try:
            if self.context['recipes_limit'] is not None:
                limit = queryset[:int(self.context['recipes_limit'])]
                return ShortRecipeSerializer(limit, many=True).data
        except KeyError:
            return ShortRecipeSerializer(queryset, many=True).data
        return ShortRecipeSerializer(queryset, many=True).data
