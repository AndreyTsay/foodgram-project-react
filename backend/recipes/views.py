from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from recipes.filters import IngredientFilter, Recipe, RecipeFilter
from recipes.models import (
    Favorite, Ingredient, IngredientRecipe, ShoppingCart, Tag
)
from recipes.permissions import IsAuthenticatedOwnerOrReadOnly
from recipes.serializers import (
    IngredientSerializer,
    RecipeSerializer, TagSerializer, ShoppingCartSerializer,
    FavoriteSerializer
)
from recipes.utils import download_pdf


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    pagination_class = None
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=('post', ),
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        user = self.request.user.id
        data = {'user': user, 'recipe': pk}
        serializer = FavoriteSerializer(data=data,
                                        context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post', ),
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = self.request.user.id
        data = {'user': user, 'recipe': pk}
        serializer = ShoppingCartSerializer(data=data,
                                            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_cart = get_object_or_404(ShoppingCart,
                                          user=user, recipe=recipe)
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('GET',),
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = self.request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)
        list = ['Список покупок:\n']
        id = []
        for recipe in shopping_cart:
            id.append(recipe.recipe.id)
        ingredients = IngredientRecipe.objects.filter(
            recipe__in=id).values(
            'ingredient__name', 'ingredient__measurement_unit').annotate(
                ingredient__amount=Sum('amount'))
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            amount = ingredient['ingredient__amount']
            measurement_unit = ingredient['ingredient__measurement_unit']
            list.append(f'{name} - {amount} {measurement_unit}\n')
        return download_pdf(list)
