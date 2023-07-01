from django.shortcuts import get_object_or_404
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import (AllowAny, IsAuthenticated)
from rest_framework.authtoken.models import Token

from api.serializers import ShowSubscriptionSerializer, SubscriptionSerializer
from users.models import CustomUser, Subscription
from users.serializers import TokenSerializer
from api.pagination import CustomPagination


class SubscriptionViewSet(views.APIView):
    """Вьюсет для модели Subscription."""

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
    """Вьюсет для отображения подписок пользователя."""

    permission_classes = [IsAuthenticated, ]
    pagination_class = CustomPagination
    serializer_class = ShowSubscriptionSerializer

    def get_queryset(self):
        user = self.request.user
        return user.subscriber.all()


class AuthToken(ObtainAuthToken):
    """Авторизация пользователя."""

    serializer_class = TokenSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {'auth_token': token.key},
            status=status.HTTP_201_CREATED)
