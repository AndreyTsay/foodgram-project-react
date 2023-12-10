from django.contrib.auth.hashers import check_password, make_password
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import User, Subscription
from .pagination import CustomPaginator
from .serializers import (
    CustomUserSerializer,
    NewPasswordSerializer,
    UserInfoSerializer,
    UserRecipesSerializer,
    UserRegistrationSerializer,
    SubscriptionSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для регистрации пользователя, просмотра списка пользователей
    и просмотра отдельного пользователя."""
    queryset = User.objects.all()
    pagination_class = CustomPaginator
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action in ['me', 'subscribe', 'subscriptions']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'list' or self.request.method == 'GET':
            return UserInfoSerializer
        elif self.action in [
            'subscribe',
            'subscriptions'
        ]:
            return UserRecipesSerializer
        return UserRegistrationSerializer

    @action(detail=False, url_path='me',
            permission_classes=(permissions.IsAuthenticated,))
    def me(self, request):
        """Метод, позволяющий посмотреть свой профиль."""
        serializer = UserInfoSerializer(request.user,
                                        context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='set_password',
            permission_classes=(permissions.IsAuthenticated,))
    def change_password(self, request):
        """Метод, позволяющий сменить пароль."""
        user = request.user
        serializer = NewPasswordSerializer(data=request.data,
                                           context={'request': request})

        serializer.is_valid(raise_exception=True)
        if check_password(serializer.data['current_password'],
                          request.user.password):
            user.password = make_password(serializer.data['new_password'])
            user.save(update_fields=["password"])
            return Response('Пароль успешно изменен.',
                            status=status.HTTP_204_NO_CONTENT)

        return Response('Неверный текущий пароль.',
                        status=status.HTTP_400_BAD_REQUEST)

    @action(methods=('get',), detail=False,
            permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        """Отображение списка подписок."""
        queryset = User.objects.filter(
            author__subscriber=request.user).prefetch_related('recipe')
        page = self.paginate_queryset(queryset)
        serializer = UserRecipesSerializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=('post',), detail=True,
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id):
        """Подписка на пользователя."""
        data = {
            'user': request.user.id,
            'author': id,
        }
        serializer = SubscriptionSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Отписаться от пользователя."""
        user = request.user
        instance = Subscription.objects.filter(subscriber=user, author=id)
        if instance.exists():
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Этой записи не существует'},
                        status=status.HTTP_400_BAD_REQUEST)
