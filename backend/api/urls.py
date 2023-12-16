from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (DownloadShoppingCart, FavouriteViewSet, FollowViewSet,
                    IngredientViewSet, RecipesViewSet, ShoppingListViewSet,
                    TagViewSet, show_follows)

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('user/<int:user_id>/',
         RecipesViewSet.as_view({'get': 'list'}), name='user-recipes'),
    path('users/subscriptions/',
         show_follows, name='users_subs'),
    path('users/<int:user_id>/subscribe/',
         FollowViewSet.as_view(), name='subscribe'),
    path('recipes/<int:recipe_id>/favorite/',
         FavouriteViewSet.as_view(), name='add_recipe_to_favorite'),
    path('recipes/<int:recipe_id>/shopping_cart/',
         ShoppingListViewSet.as_view(), name='add_recipe_to_shopping_cart'),
    path('recipes/download_shopping_cart/',
         DownloadShoppingCart.as_view(), name='dowload_shopping_cart'),
    path('', include(router.urls))
]
