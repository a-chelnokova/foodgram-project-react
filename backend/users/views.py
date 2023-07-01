"""
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.serializers import ShowSubscriptionSerializer, SubscriptionSerializer
from users.models import CustomUser, Subscription
from api.pagination import CustomPagination
"""

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import get_object_or_404

from api.serializers import (
    CustomUserSerializer,
    SubscriptionSerializer,
)
from users.models import Subscription


User = get_user_model()


class UsersViewSet(UserViewSet):
    """Вьюсет для модели пользователей."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    search_fields = ('username', 'email')
    permission_classes = (AllowAny, )

    def subscribed(self, serializer, id=None):
        Subscriptioner = get_object_or_404(User, id=id)
        if self.request.user == Subscriptioner:
            return Response({'message': 'Нельзя подписаться на себя'},
                            status=status.HTTP_400_BAD_REQUEST)
        Subscription = Subscription.objects.get_or_create(user=self.request.user,
                                                       author=Subscriptioner)
        serializer = SubscriptionSerializer(Subscription[0])
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def unsubscribed(self, serializer, id=None):
        Subscriptioner = get_object_or_404(User, id=id)
        Subscription.objects.filter(user=self.request.user,
                                 author=Subscriptioner).delete()
        return Response({'message': 'Вы успешно отписаны'},
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, serializer, id):
        if self.request.method == 'DELETE':
            return self.unsubscribed(serializer, id)
        return self.subscribed(serializer, id)

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, serializer):
        Subscriptioning = Subscription.objects.filter(user=self.request.user)
        pages = self.paginate_queryset(Subscriptioning)
        serializer = SubscriptionSerializer(pages, many=True)
        return self.get_paginated_response(serializer.data)


"""
class SubscriptionViewSet(views.APIView):
    Вьюсет для модели Subscription.

    permission_classes = [IsAuthenticated, ]
    pagination_class = CustomPagination

    def post(self, request, pk):
        author = get_object_or_404(CustomUser, pk=pk)
        user = self.request.user
        data = {
            'author': author.id,
            'user': user.id,
        }
        serializer = SubscriptionSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        author = get_object_or_404(CustomUser, pk=pk)
        subscription = get_object_or_404(
            Subscription,
            user=self.request.user,
            author=author
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionListViewSet(generics.ListAPIView):
    Вьюсет для отображения подписок пользователя.

    permission_classes = [IsAuthenticated, ]
    pagination_class = CustomPagination
    serializer_class = ShowSubscriptionSerializer

    def get_queryset(self):
        user = self.request.user
        return user.subscriber.all()
"""