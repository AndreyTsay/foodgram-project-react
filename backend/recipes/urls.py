from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet

app_name = 'recipes'

router_recipes_v1 = DefaultRouter()

router_recipes_v1.register('tags', TagViewSet, basename='tags')
router_recipes_v1.register('ingredients',
                           IngredientViewSet, basename='ingredients')
router_recipes_v1.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router_recipes_v1.urls)),
]
