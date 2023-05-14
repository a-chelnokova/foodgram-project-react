from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Модель пользователя, настроенная под приложение 'Foodgram'.
    Все поля обязательны для заполнения.
    """

    username = models.CharField(
        verbose_name='Уникальный юзернейм',
        max_length=50,
        unique=True)
    email = models.EmailField(
        'Email',
        max_length=200,
        unique=True)
    first_name = models.CharField(
        'Имя',
        max_length=150)
    last_name = models.CharField(
        'Фамилия',
        max_length=150)
    password = models.CharField(
        verbose_name='Пароль',
        max_length=128
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self) -> str:
        return f'{self.username}: {self.email}'


class Subscription(models.Model):
    """Подписки пользователей друг на друга."""
    user = models.ForeignKey(
        User,
        related_name='follower',
        verbose_name='Подписчик',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='author',
        verbose_name='Автор',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription',
            )
        ]

    def __str__(self):
        return f'Пользователь {self.user} подписался на {self.author}'
