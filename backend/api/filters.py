from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe
from users.models import CustomUser


class RecipeFilter(filters.FilterSet):
    author = filters.ModelChoiceFilter(queryset=CustomUser.objects.all())
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value is True:
            return queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if self.request.user.is_authenticated and value is True:
            return queryset.filter(customers__user=user)
        return queryset


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name', )
