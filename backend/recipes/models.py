from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from recipes import constants

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        'Название тэга', unique=True, max_length=constants.TAG_NAME_LENGHT)
    slug = models.SlugField(
        'Адрес тэга', unique=True, max_length=constants.TAG_SLUG_LENGHT)
    color = ColorField(max_length=constants.TAG_COLOR_LENGHT, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('id',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=constants.INGREDIENT_NAME_LENGTH)
    measurement_unit = models.CharField(
        'Еденицы измерения',
        max_length=constants.INGREDIENT_MEASUREMENT_LENGTH)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            ),
        )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    name = models.CharField(
        'Название рецепта', max_length=constants.MAX_RECIPE_NAME_LENGTH)
    image = models.ImageField('Изображение', upload_to='recipes/images/')
    text = models.TextField('Описание')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='recipes',
        verbose_name='Автор',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        related_name='recipes',
        through='IngredientRecipe',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes'
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(constants.COOKING_TIME_MIN_VALUE),
                    MaxValueValidator(constants.COOKING_TIME_MAX_VALUE)]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name} ({self.author})'


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_to_recipe',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_to_recipe',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveIntegerField(
        validators=(
            MinValueValidator(
                constants.AMOUNT_MIN_VALUE,
                message='Минимальное количество ингридиентов 1'),),
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique ingredient recipe'
            ),
        )


class AbstractList(models.Model):
    """Абстрактная модель для избранного и списка покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True


class Favorite(AbstractList):

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        default_related_name = 'favorites_recipe'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='uniq_favorite_user_recipe'
            ),
        )


class ShoppingCart(AbstractList):

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        default_related_name = 'carts'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='uniq_cart_user_recipe'
            ),
        )
