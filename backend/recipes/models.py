from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users import constants
from users.models import User


class Tag(models.Model):
    """Модель тегов."""
    name = models.CharField(max_length=50, unique=True)
    color = ColorField(max_length=7, unique=True)
    slug = models.SlugField(
        max_length=constants.MAX_LENGTH_124,
        unique=True,
    )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField(max_length=constants.MAX_LENGTH_124)
    measurement_unit = models.CharField(max_length=constants.MAX_LENGTH_10)

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
    name = models.CharField(max_length=constants.MAX_LENGTH_254)
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
        validators=[MinValueValidator(constants.MIN_VALUE),
                    MaxValueValidator(constants.MAX_VALUE)]
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
                constants.MIN_VALUE,
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
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    @property
    def default_related_name(self):
        """Return the default related name for the model."""
        return "%s_set" % self._meta.model_name


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