from recipes.models import (Tag, Ingredient, Recipe, IngredientToRecipe)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewset

from .permissions import IsAdminorReadOnly, IsAuthorOrReadOnly


class TagViewSet(ReadOnlyModelViewset):
    queryset = Tag.objects.all()
    serializer_class =
    permission_classes =  (IsAdminorReadOnly, )

class IngredientViewSet(ReadOnlyModelViewset):
    queryset = Ingredient.objects.all()
    serializers_class = 
    permission_classes = (IsAdminorReadOnly,)
    #fileter#

class RecipeViewSet(ModelViewSet):
    querysset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly | IsAdminorReadOnly, )
    #pagination
    #fileter#
