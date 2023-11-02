from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField('Email',
                              max_length=256, unique=True)
    first_name = models.CharField('Имя', max_length=256)
    last_name = models.CharField('Фамилия', max_length=256)

    class Meta():
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        oredring = ('id')

    def __str__(self) -> str:
        return self.email
