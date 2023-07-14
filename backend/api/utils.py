from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe


class PostDeleteMixin:
    def post_delete(self, model, model_serializer, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user

        if request.method == 'POST':
            if model.objects.filter(recipe=recipe, user=user).exists():
                raise Response(
                    {'errors': 'Рецепт уже добавлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(recipe=recipe, user=user)
            serializer = model_serializer(recipe)
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        obj = get_object_or_404(model, recipe=recipe, user=user)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def subscrib_post(request, id, model, model_user, serializer):
    """Создает подписку на автора."""

    user = request.user
    author = get_object_or_404(model_user, id=id)

    if model.objects.filter(user=user, author=author).exists():
        return Response(
            {'errors': 'Нельзя подписаться дважды'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if user == author:
        return Response(
            {'errors': 'Нельзя подписаться на самого себя'},
            status=status.HTTP_400_BAD_REQUEST
        )

    follow = model.objects.create(user=user, author=author)
    serializer = serializer(follow, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def subscrib_delete(request, pk, model, model_user):
    """Удаляет подписку на автора."""

    user = request.user
    author = get_object_or_404(model_user, id=pk)

    if not model.objects.filter(user=user, author=author).exists():
        return Response(
            {'errors': 'Вы не подписаны'},
            status=status.HTTP_400_BAD_REQUEST
        )

    follow = get_object_or_404(model, user=user, author=author)
    follow.delete()
    return Response(
        {'message': 'Подписка удалена'},
        status=status.HTTP_204_NO_CONTENT
    )
