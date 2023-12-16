from django.contrib import admin
from django.db.models import Count

from .models import Favorite, Follow, Ingredient, Recipe, ShoppingList, Tag


class RecipeAdmin(admin.ModelAdmin):
    list_filter = ('author', 'name', 'tags')
    list_display = ('name', 'author', 'get_favorite_count')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(favorite_count=Count('favorite_recipe'))

    @staticmethod
    def get_favorite_count(obj):
        return obj.favorite_count


class IngredientAdmin(admin.ModelAdmin):
    list_filter = ('name', )
    list_display = ('name', 'measurement_unit')


admin.site.register(Follow)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite)
admin.site.register(ShoppingList)
