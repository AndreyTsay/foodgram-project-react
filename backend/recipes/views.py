from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Tag, Ingredient, Recipe, Favorites, ShoppingCart
from .serializers import (
    TagSerializer,
    IngredientsSerializer,
    RecipeCreationSerializer,
    RecipeListSerializer,
    RecipeGetSerializer
)
from .permissions import IsAdminAuthorOrReadOnly
from .filters import IngredientFilter, RecipeFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра ингредиентов."""
    queryset = Ingredient.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для просмотра списка рецептов, конкретного рецепта,
    создания рецепта"""
    queryset = Recipe.objects.all()
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.request.method == 'PATCH' or self.action == 'destroy':
            permission_classes = [IsAdminAuthorOrReadOnly]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ['list', 'favorite', 'shopping_cart']:
            return RecipeListSerializer
        elif self.action == 'retrieve':
            return RecipeGetSerializer
        elif self.action == 'download_shopping_cart':
            return None
        return RecipeCreationSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=['POST', 'DELETE'], detail=False,
            url_path=r'(?P<pk>\d+)/favorite',
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, **kwargs):
        recipe = Recipe.objects.get(id=kwargs['pk'])

        if request.method == 'POST':
            if Favorites.objects.filter(
                    user=request.user, recipe=recipe).exists():
                return Response('Этот рецепт уже в списке избранного.',
                                status=status.HTTP_400_BAD_REQUEST)
            Favorites.objects.create(user=request.user, recipe=recipe)
            return Response(data=self.get_serializer(recipe).data,
                            status=status.HTTP_201_CREATED)

        if not Favorites.objects.filter(
                user=request.user, recipe=recipe).exists():
            return Response('Этот рецепт еще не в списке избранного.',
                            status=status.HTTP_400_BAD_REQUEST)
        favorite = Favorites.objects.get(
            user=request.user, recipe=recipe)
        favorite.delete()
        return Response(data=self.get_serializer(recipe).data,
                        status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', 'DELETE'], detail=False,
            url_path=r'(?P<pk>\d+)/shopping_cart',
            permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])

        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                    user=request.user, recipe=recipe).exists():
                return Response('Этот рецепт уже в списке покупок.',
                                status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            return Response(data=self.get_serializer(recipe).data,
                            status=status.HTTP_201_CREATED)

        if not ShoppingCart.objects.filter(
                user=request.user, recipe=recipe).exists():
            return Response(
                'Вы не добавляли этот рецепт в список покупок.',
                status=status.HTTP_400_BAD_REQUEST)
        shopping_cart = ShoppingCart.objects.get(
            user=request.user, recipe=recipe)
        shopping_cart.delete()
        return Response(data=self.get_serializer(recipe).data,
                        status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'], detail=False,
            url_path='download_shopping_cart',
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        recipes = Recipe.objects.filter(shopping_cart__user=self.request.user)
        recipe_list = {}

        for recipe in recipes:
            ingredients = recipe.ingredients.values(
                'name',
                'measurement_unit',
                amount=F('ingredient_for_recipe__amount')
            )
            for ingredient in ingredients:
                name = (f"{ingredient['name']}, "
                        f"({ingredient['measurement_unit']}): ")
                amount = ingredient['amount']
                recipe_list[name] = recipe_list.get(name, 0) + amount

        shopping_cart = 'Список покупок:\n'
        for key, value in recipe_list.items():
            shopping_cart += f'{key}{value}\n'

        response = HttpResponse(shopping_cart, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename=Shopping_cart.txt'
        return response
