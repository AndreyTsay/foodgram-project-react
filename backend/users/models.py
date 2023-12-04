from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from users import constants


class User(AbstractUser):
    """Кастомная модель пользователя."""
    email = models.EmailField(
        _('email address'),
        max_length=constants.MAX_EMAIL_LENGTH,
        unique=True,
        null=False
    )
    first_name = models.CharField(
        _('first name'),
        max_length=constants.MAX_FIRST_NAME_LENGTH
    )
    last_name = models.CharField(
        _('last name'),
        max_length=constants.MAX_LAST_NAME_LENGTH
    )
    password = models.CharField(max_length=constants.MAX_LENGTH_PASSWORD)

    class Meta:
        ordering = ['-email']

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')


class Subscription(models.Model):
    "Модель подписок пользователей на авторов рецептов."
    user = models.ForeignKey(
        User,
        null=True,
        on_delete=models.CASCADE,
        related_name='following_user',
    )
    author = models.ForeignKey(
        User,
        null=True,
        on_delete=models.CASCADE,
        related_name='recipe_author'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_subscription'),
            models.CheckConstraint(check=~models.Q(user=models.F('author')),
                                   name='no_self_subscription')
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
