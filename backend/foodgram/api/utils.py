from django.shortcuts import get_object_or_404
from recipes.models import Recipe
from rest_framework import status
from rest_framework.response import Response


class PostDeleteMixin:
    def post_delete(model, model_serializer, request, id):
        recipe = get_object_or_404(Recipe, id=id)

        if request.method == 'POST':
            favorite = model.objects.create(user=request.user, recipe=recipe)
            serializer = model_serializer(favorite,
                                          context={'request': request})

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            model.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
