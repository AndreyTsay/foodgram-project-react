from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import get_object_or_404

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from djoser import views
from .models import User, Subscription
from .pagination import CustomPaginator
from .serializers import (
    NewPasswordSerializer,
    UserInfoSerializer,
    UserRecipesSerializer,
    UserRegistrationSerializer,
    SubscribeSerializer,
    CustomUserSerializer
)


class UserViewSet(viewsets.ModelViewSet):
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
        elif self.action in ['subscribe', 'subscriptions']:
            return UserRecipesSerializer
        return UserRegistrationSerializer

    @action(detail=False, url_path='me',
            permission_classes=(permissions.IsAuthenticated,))
    def me(self, request):
        serializer = UserInfoSerializer(request.user,
                                        context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='set_password',
            permission_classes=(permissions.IsAuthenticated,))
    def change_password(self, request):
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


class CustomUserViewSet(views.UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPaginator

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        if request.method == 'POST':
            serializer = SubscribeSerializer(author,
                                             data=request.data,
                                             context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = get_object_or_404(Subscription,
                                             user=user,
                                             author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return None

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(subscribing__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(pages,
                                         many=True,
                                         context={'request': request})
        return self.get_paginated_response(serializer.data)
