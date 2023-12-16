from django_filters import rest_framework

from .models import Ingredient, Recipe, Tag


class IngredientFilter(rest_framework.FilterSet):
    """Фильтр для поиска ингредиента по первым символам."""
    name = rest_framework.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(rest_framework.FilterSet):
    """Фильтр рецептов по тегам, подпискам, вхождению
    в избранное и в список покупок."""
    author = rest_framework.NumberFilter(
        field_name='author',
        lookup_expr='exact'
    )
    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = rest_framework.NumberFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = rest_framework.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_anonymous:
            return Recipe.objects.none()
        if bool(value):
            return queryset.filter(
                favorite_recipe__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_anonymous:
            return Recipe.objects.none()
        if bool(value):
            return queryset.filter(
                shopping_cart__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']
