from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Модель пользователя.
    Все поля обязательны для заполнения.
    """

    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Адрес электронной почты'
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Уникальный юзернейм'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )
    password = models.CharField(
        max_length=150,
        verbose_name='Пароль'
    )

    class Meta:
        verbose_name = 'Пользователь',
        verbose_name_plural = 'Пользователи',
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Подписки на пользователей."""

    user = models.ForeignKey(
        CustomUser,
        related_name='subscriber',
        verbose_name='Подписчик',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        CustomUser,
        related_name='subscribing',
        verbose_name='Автор',
        on_delete=models.CASCADE
    )

    class Meta():
        verbose_name = 'Подписка',
        verbose_name_plural = 'Подписки',
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription'
            )
        ]
