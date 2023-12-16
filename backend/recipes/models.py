from django.db import models

from users.models import CustomUser


class Tag(models.Model):
    ORANGE = '#E26C2D'
    GREEN = '#49B64E'
    PURPLE = '#8775D2'

    COLOR_CHOICES = [
        (ORANGE, 'Оранжевый'),
        (GREEN, 'Зеленый'),
        (PURPLE, 'Фиолетовый'),
    ]
    name = models.CharField(
        max_length=200, unique=True,
        verbose_name='Название тега')
    color = models.CharField(
        max_length=7, unique=True, choices=COLOR_CHOICES,
        verbose_name='Цвет в HEX')
    slug = models.SlugField(
        max_length=200, unique=True, db_index=True,
        verbose_name='Уникальный слаг')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=200, verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT,
        related_name='recipes', verbose_name='Автор рецепта')
    name = models.CharField(max_length=200, verbose_name='Название рецепта')
    image = models.ImageField(
        verbose_name="Фото блюда", upload_to='recipes/')
    text = models.TextField(verbose_name='Описание рецепта')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes', verbose_name='Ингредиенты рецепта'
    )
    tags = models.ManyToManyField(
        Tag, related_name='recipes', blank=True,
        verbose_name='Теги рецепта')
    pub_date = models.DateTimeField(
        'Дата добавления', auto_now_add=True, db_index=True
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления')

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент в рецепте'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        null=True,
        verbose_name='Количество ингредиента'
    )

    class Meta:
        verbose_name = 'Количество ингредиента в рецепте'
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredient_recipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} in {self.recipe}'


class ShoppingList(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='purchases', verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='customers', verbose_name='Покупка')
    when_added = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата добавления'
    )

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_recipe_user_in_shopping_list'
            )
        ]


class Follow(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Пользователь подписчик')
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Пользователь на которого подписываемся')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow')
        ]

    def __str__(self):
        return f'{self.user} => {self.author}'


class Favorite(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='favorite_subscriber', verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorite_recipe',
        verbose_name='Рецепт')
    when_added = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата добавления'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_recipe_user_in_favorite'
            )
        ]
