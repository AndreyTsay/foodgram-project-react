import base64

from rest_framework import serializers
from django.core.files.base import ContentFile

from users.models import User, Subscription
from .models import (
    Tag,
    Ingredient,
    IngredientsForRecipe,
    Recipe,
    Favorites,
    ShoppingCart
)


class UserInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра профилей пользователей."""
    # Вынесен из модуля users с целью предотвращения циклического импорта.
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
    # Вынесен из модуля users с целью предотвращения циклического импорта.
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
        if value < 1:
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

        return ShoppingCart.objects.filter(
            recipe=obj, user=request.user).exists()


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
        if len(value) > 200:
            raise serializers.ValidationError(
                'имя рецепта не должно превышать 200 символов.'
            )
        return value

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Введите корректное время приготовления.'
            )
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                {'Ошибка': 'К рецепту необходимо добавить фото.'}
            )
        return value

    def validate(self, data):
        """Валидация создания рецепта - проверяет наличие
        ингредиентов, изображения и тегов."""
        ingredients = data.get('ingredient_for_recipe')
        ingredients_list = []
        if not ingredients:
            raise serializers.ValidationError(
                "Нужно добавить ингредиенты в рецепт."
            )
        for ingredient in ingredients:

            ingredient_id = ingredient.get('id')
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    {'Ошибка': 'Такого ингредиента не существует.'}
                )
            if int(ingredient['amount']) < 1:
                raise serializers.ValidationError(
                    'Укажите корректное количество ингредиентов.'
                )
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError(
                    {'Ошибка': 'Ингредиенты не должны повторяться.'}
                )
            ingredients_list.append(ingredient_id)

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                "Необходимо указать хотя бы один тег."
            )
        tags_list = []
        for tag in tags:

            if tag in tags_list:
                raise serializers.ValidationError(
                    {'Ошибка': 'Теги не должны повторяться.'}
                )
            tags_list.append(tag)

        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredient_for_recipe')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient in ingredients:
            IngredientsForRecipe.objects.create(
                ingredient_id=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount')
            )

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
        ingredients = validated_data.pop('ingredient_for_recipe')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()

        for ingredient in ingredients:
            IngredientsForRecipe.objects.create(
                ingredient_id=ingredient.get('id'),
                recipe=instance,
                amount=ingredient.get('amount')
            )
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
