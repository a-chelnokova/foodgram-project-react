from django.shortcuts import get_object_or_404
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from api.serializers import ShowSubscriptionSerializer, SubscriptionSerializer
from users.models import CustomUser, Subscription
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

    permission_classes = [AllowAny, ]
    pagination_class = CustomPagination
    serializer_class = ShowSubscriptionSerializer

    def get_queryset(self):
        user = self.request.user
        return user.subscriber.all()
