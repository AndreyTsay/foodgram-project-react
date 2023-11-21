from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db.models import F, Q


class User(AbstractUser):
    """Кастомная модель пользователя."""
    email = models.EmailField(
        _('email address'),
        max_length=254,
        unique=True,
        null=False
    )
    first_name = models.CharField(
        _('first name'),
        max_length=150
    )
    last_name = models.CharField(
        _('last name'),
        max_length=150
    )
    password = models.CharField(max_length=150)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_user'
            ),
        ]

    def __str__(self):
        return self.username


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
            models.CheckConstraint(check=~Q(user=F('author')),
                                   name='no_self_subscription')
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
