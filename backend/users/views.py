from django.shortcuts import get_object_or_404
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers import ShowSubscriptionSerializer, SubscriptionSerializer
from users.models import CustomUser, Subscription
from api.pagination import CustomPagination


class SubscriptionViewSet(views.APIView):
    """Вьюсет для модели Subscription."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('id', None)
        author = get_object_or_404(CustomUser, pk=pk)

        sub = Subscription(author=author, user=request.user)
        sub.save()

        serializer = SubscriptionSerializer(author,
                                            context={'request': request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        author = get_object_or_404(CustomUser, id=id)
        subscription = get_object_or_404(Subscription, user=request.user,
                                         author=author)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionListViewSet(generics.ListAPIView):
    """Вьюсет для отображения подписок пользователя."""

    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request):
        user = request.user
        queryset = CustomUser.objects.filter(author__user=user)
        page = self.paginate_queryset(queryset)
        serializer = ShowSubscriptionSerializer(page, many=True,
                                                context={'request': request})
        return self.get_paginated_response(serializer.data)
