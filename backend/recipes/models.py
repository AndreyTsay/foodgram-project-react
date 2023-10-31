from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tags(models.Model):
    name = models.CharField('Название', unique=True, max_length=256)
    color =
    slug = models.SlugField(max_length=256)


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=256)
    unit_of_mesurement = models.CharField('Единицика измерения', max_length=256)
    
    class Meta:
        verbose_name = 'Ингридиент'
        verbouse_name_plural = 'Ингридиенты'
        ordering = ['name']
    def __str__(self) -> str:
        return f'{self.name}, {self.unit_of_mesurement}'


class Recipes(models.Model):
    id = models.IntegerField
    tags = models.ForeignKey(Tags, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    ingridients = 
    text = models.CharField
    image = 
    cooking_time = models.IntegerField > 1


    



# Create your models here.
