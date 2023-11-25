from django_filters import rest_framework

from .models import Ingredient, Recipe, Tag


class IngredientFilter(rest_framework.FilterSet):
    name = rest_framework.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(rest_framework.FilterSet):
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
        method='object_is_exist_filter'
    )
    is_in_shopping_cart = rest_framework.NumberFilter(
        method='object_is_exist_filter'
    )

    def object_is_exist_filter(self, queryset, name, value):
        lookup = '__'.join([name, 'user'])
        if self.request.user.is_anonymous:
            return queryset
        if bool(value):
            return queryset.filter(**{lookup: self.request.user})
        return queryset

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']
