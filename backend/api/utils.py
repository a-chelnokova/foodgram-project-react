from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from recipes.models import Recipe
from users.models import CustomUser


class PostDeleteMixin:
    def post_delete(self, model, model_serializer, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user

        if request.method == 'POST':
            if model.objects.filter(recipe=recipe, user=user).exists():
                raise ValidationError('Рецепт уже добавлен')
            model.objects.create(recipe=recipe, user=user)
            serializer = model_serializer(recipe)
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        obj = get_object_or_404(model, recipe=recipe, user=user)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserCreateMixin:
    def create(self, validated_data):
        try:
            user = self.perform_create(validated_data)
        except IntegrityError:
            self.fail('cannot_create')
        return user

    def perform_create(self, validated_data):
        with transaction.atomic():
            user = CustomUser.objects.create_user(**validated_data)
        return user


def subscrib_post(request, id, model, model_user, serializer):
    """Создает новую подписку"""

    user = request.user
    author = get_object_or_404(model_user, id=id)

    if model.objects.filter(user=user, following=author).exists():
        return Response(
            {'errors': 'Нельзя подписаться дважды'},
            status=status.HTTP_400_BAD_REQUEST)
    if user == author:
        return Response(
            {'errors': 'Нельзя подписаться на самого себя'},
            status=status.HTTP_400_BAD_REQUEST)

    follow = model.objects.create(user=user, following=author)
    serializer = serializer(follow, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def subscrib_delete(request, pk, model, model_user):
    """Удаляет существующую подписку"""

    user = request.user
    author = get_object_or_404(model_user, id=pk)

    if not model.objects.filter(user=user, following=author).exists():
        return Response(
            {'errors': 'Вы не подписаны на данного пользователя'},
            status=status.HTTP_400_BAD_REQUEST)

    follow = get_object_or_404(model, user=user, following=author)
    follow.delete()
    return Response(
        {'message': 'Подписка удалена'},
        status=status.HTTP_204_NO_CONTENT
    )
