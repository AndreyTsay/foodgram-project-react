from django.contrib.auth import get_user_model
from django.db import models
from colorfield.fields import ColorField

User = get_user_model()


class Tag(models.Model):
    name = models.CharField('Название', unique=True, max_length=256)
    color = ColorField(format='hex')
    slug = models.SlugField(max_length=256)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=256)
    unit_of_mesurement = models.CharField('Единицика измерения', max_length=256)

    class Meta:
        verbose_name = 'Ингридиент'
        verbouse_name_plural = 'Ингридиенты'
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name}, {self.unit_of_mesurement}'


class Recipe(models.Model):
    id = models.IntegerField
    tags = models.ForeignKey(Tag, verbose_name='Теги',
                             related_name='recipes', on_delete=models.CASCADE)
    name = models.CharField('Название',max_length=256)
    author = models.ForeignKey(User, related_name='recipes',
                               verbose_name='Автор', on_delete=models.CASCADE)
    ingridients = models.ForeignKey(Ingredient)
    text = models.CharField('Описание рецепта', max_length=256)
    image = models.ImageField('Изображение',
                              blank=True, null=True, upload_to='static/recipe/')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления')
    pub_date = models.DateField('Дата публикации', auto_now=True)


class IngredientToRecipe():
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe')
    ingridient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='ingredient')
    amount = models.IntegerField(default=1, verbose_name='Количество')

    class Meta:
        verbose_name = 'Количесво ингридиента'
        verbose_name_plural = 'Количесво игриентов'
        ordering = ['id']
