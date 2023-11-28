from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    page_size = settings.RECIPE_PAGE_SIZE
