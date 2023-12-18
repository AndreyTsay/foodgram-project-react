from django_filters import rest_framework as rest_framework_filter
from rest_framework.filters import SearchFilter
from recipes.models import Recipe, User


class RecipeFilter(rest_framework_filter.FilterSet):
    author = rest_framework_filter.ModelChoiceFilter(
        queryset=User.objects.all()
    )
    tags = rest_framework_filter.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_favorited = rest_framework_filter.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = rest_framework_filter.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        return queryset.filter(favorites__user=self.request.user.id)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return queryset.filter(carts__user=self.request.user.id)

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')


class IngredientFilter(SearchFilter):
    search_param = 'name'
