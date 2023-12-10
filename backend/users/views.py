from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import User, Subscription
from .pagination import CustomPaginator
from .serializers import (
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

    @action(methods=['POST'], detail=False,
            url_path=r'(?P<pk>\d+)/subscribe',
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id):
        """Подписка на пользователя."""
        data = {
            'subscriber': request.user.id,
            'author': id,
        }
        serializer = SubscriptionSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['pk'])
        serializer = UserRecipesSerializer(author,
                                           context={'request': request})
        subscription = Subscription.objects.filter(
            user=request.user, author=author).first()
        if not subscription:
            return Response('Вы не подписаны на этого пользователя.',
                            status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(serializer.data,
                        status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'], detail=False,
            url_path='subscriptions',
            permission_classes=(permissions.IsAuthenticated,),
            pagination_class=CustomPaginator)
    def subscriptions(self, request):
        authors = User.objects.filter(
            recipe_author__user=request.user).prefetch_related('recipes')
        page = self.paginate_queryset(authors)

        serializer = UserRecipesSerializer(
            page, many=True,
            context={'request': request})

        return self.get_paginated_response(serializer.data)
