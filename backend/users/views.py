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
        Sub = Subscription.objects.get_or_create(
            user=self.request.user,
            author=Subscriptioner
        )
        serializer = SubscriptionSerializer(Sub[0])
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
