from django.contrib import admin

from .models import Tag, Ingredient, Recipe


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'in_favorites',)
    search_fields = ('name',)
    list_filter = ('name', 'author',)
    empty_value_display = '-пусто-'

    @admin.display(description='Добавления в избранное')
    def in_favorites(self, obj):
        return obj.favorite_recipe.count()


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
