from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet

app_name = 'users'

router_users_v1 = DefaultRouter()

router_users_v1.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router_users_v1.urls)),
    path('auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]
