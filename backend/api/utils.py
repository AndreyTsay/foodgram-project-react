from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe

from .serializers import AddFavouriteRecipeSerializer


def get_post(request, recipe_id, acted_model):
    user = request.user
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if acted_model.objects.filter(user=user, recipe=recipe).exists():
        return Response(
            'Рецепт уже добавлен',
            status=status.HTTP_400_BAD_REQUEST)
    acted_model.objects.create(user=user, recipe=recipe)
    serializer = AddFavouriteRecipeSerializer(recipe)
    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED)


def get_delete(request, recipe_id, acted_model):
    user = request.user
    recipe = get_object_or_404(Recipe, id=recipe_id)
    favorite_obj = get_object_or_404(acted_model, user=user, recipe=recipe)
    if not favorite_obj:
        return Response(
            'Рецепт не был добавлен',
            status=status.HTTP_400_BAD_REQUEST)
    favorite_obj.delete()
    return Response(
        'Удалено', status=status.HTTP_204_NO_CONTENT)
