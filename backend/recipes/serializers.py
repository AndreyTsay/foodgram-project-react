import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

from users import constants
from users.models import Subscription, User

from .models import (
    Favorites,
    Ingredient,
    IngredientsForRecipe,
    Recipe,
    ShoppingCart,
    Tag
)
from .utils import bulk_create_ingredients_for_recipe


class UserInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра профилей пользователей."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False

        return Subscription.objects.filter(
            author=obj, user=request.user).exists()


class UserShortInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения пользователя на главной странице
    рецептов."""
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientForGettingRecipe(serializers.ModelSerializer):
    """Сериализатор для получения ингредиентов в рецепте."""
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id',
        queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientsForRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientForRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиента в рецепт."""
    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientsForRecipe
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value < constants.MIN_VALUE:
            raise serializers.ValidationError(
                'Укажите корректное количество ингредиентов.'
            )
        return value


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения информации о рецепте."""
    tags = TagSerializer(many=True)
    ingredients = IngredientForGettingRecipe(
        source='ingredient_for_recipe',
        many=True,
        read_only=True
    )
    author = UserInfoSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'tags', 'ingredients', 'cooking_time',
                  'author', 'image', 'text',
                  'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False

        return Favorites.objects.filter(recipe=obj, user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False

        recipe = obj
        user = request.user

        if ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
            return True
        return False


class RecipeCreationSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта"""
    name = serializers.CharField(required=True)
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = IngredientForRecipeSerializer(
        source='ingredient_for_recipe',
        many=True
    )
    image = Base64ImageField()
    author = UserInfoSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'tags', 'ingredients',
                  'cooking_time', 'text', 'image')

    def validate_name(self, value):
        if len(value) > constants.MAX_RECIPE_NAME_LENGTH:
            raise serializers.ValidationError(
                'Имя рецепта не может быть более 254 символов.'
            )
        return value

    def validate_cooking_time(self, value):
        if value < constants.COOKING_TIME_MIN_VALUE or (
                value > constants.COOKING_TIME_MAX_VALUE):
            raise serializers.ValidationError(
                'Укажите корректное время приготовления.'
            )
        return value

    def validate(self, data):
        """Валидация создания рецепта - проверяет наличие
        ингредиентов, изображения и тегов."""
        ingredients = self.initial_data.get('ingredients')
        ingredients_list = []
        if not ingredients:
            raise serializers.ValidationError(
                "Нужно добавить ингредиенты в рецепт."
            )
        for ingredient in ingredients:

            value = Ingredient.objects.filter(id=ingredient['id'])
            if not value.exists():
                raise serializers.ValidationError(
                    {'Ошибка': 'Такого ингредиента не существует.'}
                )
            if int(ingredient['amount']) < 1:
                raise serializers.ValidationError(
                    'Укажите корректное количество ингредиентов.'
                )
            if value in ingredients_list:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.'
                )
            ingredients_list.append(value)

        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                "Необходимо указать хотя бы один тег."
            )
        tags_list = []
        for tag in tags:

            if tag in tags_list:
                raise serializers.ValidationError(
                    'Теги не должны повторяться.'
                )
            tags_list.append(tag)

        image = self.initial_data.get('image')
        if not image:
            raise serializers.ValidationError(
                "К рецепту необходимо добавить изображение."
            )
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredient_for_recipe')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        bulk_create_ingredients_for_recipe(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        instance.text = validated_data.get(
            'text',
            instance.text
        )
        instance.image = validated_data.get('image', instance.image)
        ingredients_data = validated_data.pop('ingredient_for_recipe')
        tags_data = validated_data.pop('tags')

        instance.tags.clear()
        instance.tags.set(tags_data)
        instance.ingredients.clear()
        bulk_create_ingredients_for_recipe(instance, ingredients_data)

        instance.save()

        return instance

    def to_representation(self, instance):
        request = {'request': self.context.get('request')}
        recipe_for_view = RecipeGetSerializer(instance, context=request)
        return recipe_for_view.data


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения основной информации о рецепте
    на главной странице."""
    tags = TagSerializer(many=True)
    author = UserShortInfoSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'image', 'name', 'tags', 'cooking_time', 'author',
                  'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False

        return Favorites.objects.filter(recipe=obj, user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False

        return ShoppingCart.objects.filter(
            recipe=obj, user=request.user).exists()


class RecipeContextSerializer(serializers.ModelSerializer):
    "Сериализатор для отображения профиля рецепта в профиле авторов."

    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'image',
                  'cooking_time')
