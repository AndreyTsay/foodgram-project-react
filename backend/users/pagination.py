from rest_framework.pagination import PageNumberPagination


class CustomPaginator(PageNumberPagination):
    """Кастомный пагинатор для вывода определенного количества страниц."""
    page_size = 6
    page_size_query_param = 'limit'
