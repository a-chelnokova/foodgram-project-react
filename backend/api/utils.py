from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe
from users.models import CustomUser


class PostDeleteMixin:
    def post_delete(self, model, model_serializer, request, id):
        recipe = get_object_or_404(Recipe, id=id)

        if request.method == 'POST':
            favorite = model.objects.create(user=request.user, recipe=recipe)
            serializer = model_serializer(favorite,
                                          context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        model.objects.filter(user=request.user, recipe=recipe).delete()
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
