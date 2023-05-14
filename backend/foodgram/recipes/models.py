from core.enums import Limits, Tuples
from django.contrib.auth import get_user_model
from django.core import validators
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Tag(models.Model):
    """
    Модель тегов для рецептов,
    связано с Recipe через Many-to-Many
    """

    ORANGE = '#FFA500'
    GREEN = '#008000'
    PURPLE = '#800080'

    COLOR_CHOICES = [
        (ORANGE, 'Оранжевый'),
        (GREEN, 'Зеленый'),
        (PURPLE, 'Фиолетовый'),
    ]
    
    name = models.CharField(max_length=200, unique=True,
                            db_index=True,
                            verbose_name='Название тега')
    
    color = models.CharField(max_length=7, unique=True,
                             db_index=False,
                             choices=COLOR_CHOICES,
                             verbose_name='Цвет в HEX')
    
    slug = models.SlugField(max_length=200, unique=True,
                            db_index=False,
                            verbose_name='Уникальный слаг')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """
    Модель ингредиентов для рецептов,
    связано с Recipe через Many-to-Many
    """

    name = models.CharField(verbose_name='Название ингредиента')
    measurement_unit = models.CharField(verbose_name='Единица измерения',
                                        max_length=24)

    class Meta:
        ordering = ('name', )
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique ingredient')
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """
    Модель для рецептов.
    Основная модель приложения, описывающая рецепты.
    """

    pub_date = models.DateTimeField(
        'Дата создания',
        editable=False,
        auto_now_add=True
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
        null=True,
    )

    name = models.CharField(max_length=200, db_index=True,
                            verbose_name='Название')

    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Список ингредиентов',
        related_name='recipes',
        through='recipes.AmountIngredient',
    )

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тег',
    )

    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipe_images/'
    )

    text = models.TextField(verbose_name='Описание')

    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=[validators.MinValueValidator(
            1, message='Время приготовления должно быть не менее 1 минуты!'
        )]
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'author'),
                name='unique_for_author',
            ),
        )
    
    def __str__(self) -> str:
        return f'{self.name}. Автор: {self.author.username}'

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        image = image.open(self.image.path)
        image = image.resize(Tuples.RECIPE_IMAGE_SIZE)
        image.save(self.image.path)


class AmountIngredient(models.Model):
    """
    Количество ингредиентов в блюде.
    Модель связывает Recipe и Ingredient с указанием количества ингридиента.
    """

    recipe = models.ForeignKey(
        Recipe,
        verbose_name = 'В каких рецептах',
        related_name = 'ingredient',
        on_delete = models.CASCADE,
    )
    ingredients = models.ForeignKey(
        Ingredient,
        verbose_name = 'Связанные ингредиенты',
        related_name = 'recipe',
        on_delete = models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name = 'Количество',
        default = 0,
        validators = (
            MinValueValidator(
                Limits.MIN_AMOUNT_INGREDIENTS,
                'Для готовки нужны ингредиенты',
            ),
            MaxValueValidator(
                Limits.MAX_AMOUNT_INGREDIENTS,
                'Слишком много ингредиентов!',
            ),
        ),
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Количество ингридиентов'
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.amount} {self.ingredients}'


class Favorite(models.Model):
    """
    Избранные рецепты.
    Модель связывает Recipe и User.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='in_favorites',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_favorite_unique'
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} -> {self.recipe}'


class ShoppingList(models.Model):
    """
    Список покупок, созданный на основе необходимых
    ингредиентов для выбранных рецептов.
    Модель связывает Recipe и User.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='in_shopping_list'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_list'
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_shopping_list_unique'
            ),
        )
    
    def __str__(self) -> str:
        return f'{self.user} -> {self.recipe}'
