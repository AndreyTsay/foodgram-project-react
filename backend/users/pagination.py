from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class UsersPagination(PageNumberPagination):
    page_size = settings.USER_PAGE_SIZE
