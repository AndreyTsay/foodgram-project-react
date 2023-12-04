from colorfield.fields import ColorField
from django import constants
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    """Модель тегов."""
    name = models.CharField(
        max_length=constants.TAG_NAME_LENGHT, unique=True)
    color = ColorField(max_length=constants.TAG_COLOR_LENGHT, unique=True)
    slug = models.SlugField(
        max_length=constants.TAG_SLUG_LENGHT,
        unique=True,
    )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField(max_length=constants.INGREDIENT_NAME_LENGTH)
    measurement_unit = models.CharField(
        max_length=constants.INGREDIENT_MEASUREMENT_LENGTH)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_unit'
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=constants.MAX_RECIPE_NAME_LENGTH)
    image = models.ImageField(
        upload_to='recipes/images/',
        default=None
    )
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientsForRecipe',
        related_name='recipe_ingredients'
    )
    tags = models.ManyToManyField(Tag, related_name='recipe_tag')
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(constants.COOKING_TIME_MIN_VALUE),
                    MaxValueValidator(constants.COOKING_TIME_MAX_VALUE)]
    )

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return self.name


class IngredientsForRecipe(models.Model):
    """Вспомогательная модель для добавления ингредиентов в рецепт."""
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredient_for_recipe',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='ingredient_for_recipe',
        on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(
                    constants.AMOUNT_MIN_VALUE,
                    message='Минимальное количество ингридиентов 1'),),
        verbose_name='Количество',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredient_recipe'
            )
        ]

    def __str__(self):
        return f'{self.recipe}: {self.ingredient}'


class AbstractList(models.Model):
    """Абстрактная модель для избранного и списка покупок."""
    user = models.ForeignKey(
        User,
        related_name="%(app_label)s_%(class)s_related",
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="%(app_label)s_%(class)s_related",
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True


class Favorites(AbstractList):
    """Модель для добавления рецепта в избранное."""

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]

    def __str__(self):
        return f'Рецепт {self.recipe.name} в избранном у {self.user.username}'


class ShoppingCart(AbstractList):
    """Модель для списка покупок."""

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_cart'
            )
        ]

    def __str__(self):
        return (f'Рецепт {self.recipe.name} в списке покупок'
                f' у {self.user.username}')
