from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TagViewSet, IngredientViewSet, RecipeViewSet

app_name = 'recipes'

router_recipes_v1 = DefaultRouter()

router_recipes_v1.register('tags', TagViewSet, basename='tags')
router_recipes_v1.register('ingredients',
                           IngredientViewSet, basename='ingredients')
router_recipes_v1.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router_recipes_v1.urls)),
]
