from django.shortcuts import get_object_or_404
from rest_framework import generics, status, views
from rest_framework.generics import (ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.permissions import AuthorOrReadOnly
from api.serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                             ShowSubscriptionSerializer,
                             SubscriptionSerializer)
from users.models import CustomUser, Subscription


class ListCreateUserView(ListCreateAPIView):
    """
    Вьюсет для модели CustomUser.
    Обрабатывает GET и POST запросы.
    """

    queryset=CustomUser.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomUserCreateSerializer
        else:
            return CustomUserSerializer

    def perform_create(self, serializer):
        serializer.save()


class RetrieveUpdateDestroyUserView(RetrieveUpdateDestroyAPIView):
    """
    Вьюсет для модели CustomUser.
    Обрабатывает запросы GET, PUT, PATCH и DELETE.
    """

    queryset=CustomUser.objects.all()
    serializer_class=CustomUserSerializer
    permission_classes=[AuthorOrReadOnly]


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
    serializer_class = ShowSubscriptionSerializer

    def get_queryset(self):
        user = self.request.user
        return Subscription.objects.filter(user=user)
