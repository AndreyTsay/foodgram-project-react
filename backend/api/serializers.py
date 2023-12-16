from djoser.serializers import UserSerializer as BaseUserSerializer
from django.core.validators import MinValueValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (CustomUser, Favorite, Follow, Ingredient,
                            IngredientInRecipe, Recipe, ShoppingList, Tag)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('__all__')


class FollowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = ('__all__')


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'purchases')


class AddFavouriteRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingListRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ListRecipeUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()


class IngredientInRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = IngredientInRecipe
        fields = '__all__'


class IngredientInRecipeSerializerToCreateRecipe(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class ListRecipeSerializer(serializers.ModelSerializer):
    author = ListRecipeUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_ingredients(self, obj):
        qs = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializerToCreateRecipe(qs, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return Favorite.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return ShoppingList.objects.filter(recipe=obj, user=user).exists()


class RecipeSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(
        max_length=None,
        required=True,
        allow_empty_file=False,
        use_url=True,
    )
    author = ListRecipeUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'

    extra_kwargs = {
        'cooking_time': {'validators': [MinValueValidator(1)]}
    }


class ShowFollowerRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShowFollowersSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField('recipes_limit_followers')
    recipes_count = serializers.SerializerMethodField('count_author_recipes')
    is_subscribed = serializers.SerializerMethodField('check_if_subscribed')

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def recipes_limit_followers(self, user):
        request = self.context.get('request')
        if request.query_params.get('recipes_limit'):
            recipes_limit = int(request.query_params.get('recipes_limit'))
            query = Recipe.objects.filter(author=user)[:recipes_limit]
        else:
            query = Recipe.objects.filter(author=user)
        serializer = ShowFollowerRecipeSerializer(
            query, read_only=True, many=True
        )
        return serializer.data

    def count_author_recipes(self, user):
        return user.recipes.count()

    def check_if_subscribed(self, user):
        current_user = self.context.get('current_user')
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=current_user).exists()


class ShowIngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'amount', )


class UserSerializerModified(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()


class AddIngredientToRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=True)
    author = UserSerializerModified(read_only=True)
    ingredients = AddIngredientToRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def validate(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        for ingredient in ingredients_data:
            if ingredient['amount'] <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше нуля!')
        validated_data['ingredients'] = ingredients_data
        return validated_data

    def add_ingredient(self, validated_data, recipe):
        ingredients_data = validated_data.pop('ingredients')
        for new_ingredient in ingredients_data:
            IngredientInRecipe.objects.get_or_create(
                ingredient=Ingredient.objects.get(id=new_ingredient['id']),
                recipe=recipe,
                amount=new_ingredient['amount']
            )

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(
            author=author, **validated_data)
        recipe.save()
        recipe.tags.set(tags_data)
        validated_data['ingredients'] = ingredients_data
        self.add_ingredient(validated_data, recipe)
        return recipe

    def update(self, recipe, validated_data):
        IngredientInRecipe.objects.filter(recipe=recipe).delete()
        self.add_ingredient(validated_data, recipe)
        return super().update(recipe, validated_data)

    def to_representation(self, instance):
        return ListRecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        ).data
