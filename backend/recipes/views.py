from django.db.models import F
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .models import Favorites, Ingredient, Recipe, ShoppingCart, Tag
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly, AuthUserDelete
from .serializers import (
    IngredientsSerializer,
    RecipeCreationSerializer,
    RecipeGetSerializer,
    RecipeListSerializer,
    TagSerializer
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра ингредиентов."""
    queryset = Ingredient.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
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
            permission_classes = [IsOwnerOrReadOnly, IsAdminOrReadOnly]
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

    @action(detail=True, methods=['POST'],
            url_path='shopping_cart', permission_classes=[AuthUserDelete])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if user.shopping_cart.filter(recipe=recipe).exists():
            return Response(
                {'detail': 'Этот рецепт уже в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST)

        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = RecipeListSerializer(recipe, context={'request': request})
        return Response(
            {'detail': 'Рецепт успешно добавлен в список покупок.',
             'recipe': serializer.data},
            status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, *args, **kwargs):
        recipe = self.get_object()
        user = request.user
        objects = user.shopping_cart.filter(recipe=recipe)

        if not objects.exists():
            return Response(
                {'detail': 'Этот рецепт не в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST)

        objects.delete()
        serializer = RecipeListSerializer(recipe, context={'request': request})
        return Response(
            {'detail': 'Рецепт успешно удален из списка покупок.',
             'recipe': serializer.data},
            status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'], detail=False,
            url_path='download_shopping_cart',
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        recipes = Recipe.objects.filter(
            shopping_cart__user=self.request.user).order_by('name')
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
