from rest_framework.pagination import PageNumberPagination


class UsersPagination(PageNumberPagination):
    page_size = 10


class RecipePagination(PageNumberPagination):
    page_size = 6
