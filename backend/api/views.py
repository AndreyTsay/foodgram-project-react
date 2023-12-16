import django_filters.rest_framework
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (CustomUser, Favorite, Follow, Ingredient,
                            IngredientInRecipe, Recipe, ShoppingList, Tag)
from users.models import CustomUser

from .filters import IngredientFilter, RecipeFilter
from .paginators import PageNumberPaginatorModified
from .permissions import AdminOrAuthorOrReadOnly
from .serializers import (CreateRecipeSerializer,
                          IngredientSerializer, ListRecipeSerializer,
                          ShowFollowersSerializer, TagSerializer)
from .utils import get_post, get_delete


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    filter_class = RecipeFilter
    pagination_class = PageNumberPaginatorModified
    permission_classes = [AdminOrAuthorOrReadOnly, ]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ListRecipeSerializer
        return CreateRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def get_queryset(self):
        queryset = Recipe.objects.all()
        author_email = self.kwargs.get('user_id')

        if author_email:
            queryset = queryset.filter(author__email=author_email)

        return queryset


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = [AllowAny, ]
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend, ]
    filter_class = IngredientFilter
    pagination_class = None


@api_view(['GET', ])
@permission_classes([IsAuthenticated])
def show_follows(request):
    user_obj = CustomUser.objects.filter(following__user=request.user)
    paginator = PageNumberPagination()
    paginator.page_size = 6
    result_page = paginator.paginate_queryset(user_obj, request)
    serializer = ShowFollowersSerializer(
        result_page, many=True, context={
            'current_user': request.user, 'request': request
        })
    return paginator.get_paginated_response(serializer.data)


class FollowViewSet(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, user_id):
        user = request.user
        author = get_object_or_404(CustomUser, id=user_id)
        if Follow.objects.filter(user=user, author=author).exists():
            return Response(
                'Вы уже подписаны',
                status=status.HTTP_400_BAD_REQUEST)
        Follow.objects.create(user=user, author=author)
        serializer = ShowFollowersSerializer(author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        user = request.user
        author = get_object_or_404(CustomUser, id=user_id)
        follow = get_object_or_404(Follow, user=user, author=author)
        follow.delete()
        return Response(
            'Удалено', status=status.HTTP_204_NO_CONTENT)


class FavouriteViewSet(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, recipe_id):
        return get_post(request, recipe_id, Favorite)

    def delete(self, request, recipe_id):
        return get_delete(request, recipe_id, Favorite)


class ShoppingListViewSet(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, recipe_id):
        return get_post(request, recipe_id, ShoppingList)

    def delete(self, request, recipe_id):
        return get_delete(request, recipe_id, ShoppingList)


class DownloadShoppingCart(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        recipe_ids = request.user.purchases.values_list('recipe__id',
                                                        flat=True)
        ingredients = IngredientInRecipe.objects.filter(recipe__in=recipe_ids)

        if not ingredients.exists():
            return HttpResponse("You haven't purchased any recipes.",
                                status=400)

        buying_list = {}
        ingredients = ingredients.values(
            'ingredient',
            'ingredient__name',
            'ingredient__measurement_unit'
        )
        ingredients = ingredients.annotate(sum_amount=Sum('amount'))

        for ingredient in ingredients:
            sum_amount = ingredient.get('sum_amount')
            name = ingredient.get('ingredient__name')
            measurement_unit = ingredient.get('ingredient__measurement_unit')

            if sum_amount > 0 and name not in buying_list:
                buying_list[name] = {
                    'measurement_unit': measurement_unit,
                    'sum_amount': sum_amount
                }

        wishlist = []
        for item in buying_list:
            wishlist.append(f'{item} - {buying_list[item]["sum_amount"]} '
                            f'{buying_list[item]["measurement_unit"]} \n')

        response = HttpResponse(wishlist, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="wishlist.txt"'
        return response
