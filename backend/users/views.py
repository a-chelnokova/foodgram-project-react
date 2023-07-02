from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from djoser.views import UserViewSet

from api.pagination import CustomPagination
from api.utils import subscrib_delete, subscrib_post
from users.models import Subscription, CustomUser
from users.serializers import SubscriptionSerializer


class CustomUserViewSet(UserViewSet):
    """ViewSet для работы с пользователями сервиса FoodGram."""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = CustomUser.objects.all().order_by('-date_joined')
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, ],
        url_name='subscribe',
        url_path='subscribe')
    def subscribe(self, request, id=None):
        """Подписывает пользователя на другого пользователя."""

        if request.method == 'POST':
            return subscrib_post(request, id, Subscription, CustomUser,
                                 SubscriptionSerializer)
        return subscrib_delete(request, id, Subscription, CustomUser)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),)
    def subscriptions(self, request):
        """
        Возвращает список пользователей, на которых
        подписан текущий пользователь.
        """
        user = request.user
        queryset = Subscription.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages,
            many=True,
            context={'request': request}
        )

        response_data = {
            'count': len(pages),
            'next': self.paginator.get_next_link(),
            'previous': self.paginator.get_previous_link(),
            'results': serializer.data}
        return Response(response_data)
