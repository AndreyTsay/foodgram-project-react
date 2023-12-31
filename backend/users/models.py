from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models

from users import constants


class User(AbstractUser):
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')
    USERNAME_FIELD = 'email'
    username_validator = UnicodeUsernameValidator()
    email = models.EmailField(
        verbose_name='адрес электронной почты',
        blank=False,
        unique=True,
        max_length=constants.MAX_EMAIL_LENGTH,
        error_messages={
            'unique': 'Такой адрес электронной почты уже зарегистрирован.'
        },
    )
    username = models.CharField(
        verbose_name='логин',
        max_length=constants.MAX_LENGTH_USERNAME,
        unique=True,
        help_text='Не более 150 символов.',
        validators=[username_validator],
        error_messages={
            'unique': 'Пользователь с таким именем уже зарегистрирован.'
        },
    )
    first_name = models.CharField(
        verbose_name='имя', max_length=constants.MAX_FIRST_NAME_LENGTH)
    last_name = models.CharField(
        verbose_name='фамилия', max_length=constants.MAX_LAST_NAME_LENGTH)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.username == 'me':
            return ValidationError('Username не может быть "me".')
        return super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.is_superuser

    def get_full_name(self):
        return f'{self.first_name} + {self.last_name}'

    def get_short_name(self):
        return f'{self.username[:15]}'

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = (
            models.CheckConstraint(
                check=~models.Q(username='me'),
                name='Пользователь не может быть назван me!',
            ),
        )

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_follow'
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F('user')),
                name='Пользователь не может подписаться на самого себя',
            ),
        )
