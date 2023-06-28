from django.core.validators import MinValueValidator
from django.db import models

from users.models import CustomUser


class Tag(models.Model):
    """Теги для рецептов."""

    ORANGE = '#FFA500'
    GREEN = '#008000'
    PURPLE = '#800080'

    COLOR_CHOICES = [
        (ORANGE, 'Оранжевый'),
        (GREEN, 'Зеленый'),
        (PURPLE, 'Фиолетовый'),
    ]

    name = models.CharField(max_length=50, unique=True,
                            verbose_name='Название тега')

    color = models.CharField(max_length=50, choices=COLOR_CHOICES,
                             verbose_name='Цвет')

    slug = models.SlugField(max_length=50, unique=True,
                            db_index=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег',
        verbose_name_plural = 'Теги',
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ингредиенты для рецептов."""

    name = models.CharField(max_length=150, unique=True,
                            verbose_name='Название ингредиента')

    measurement_unit = models.CharField(max_length=150,
                                        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент',
        verbose_name_plural = 'Ингредиенты',
        ordering = ['name']

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class RecipeIngredient(models.Model):
    """Необходимое количество ингредиентов."""

    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE,
                               verbose_name='Рецепт')

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   verbose_name='Ингредиент')

    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        default=1,
        validators=[MinValueValidator(1, message='Минимальное количество-1')]
    )

    class Meta:
        verbose_name = 'Количество ингредиента',
        verbose_name_plural = 'Количество ингредиентов',
        ordering = ['ingredient']
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'],
                                    name='recipe_ingredient_unique')]


class RecipeTag(models.Model):
    """Модель связи тега и рецепта."""

    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE,
                               verbose_name='Рецепт')

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,
                            verbose_name='Тег')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'tag'],
                                    name='recipe_tag_unique')]


class Recipe(models.Model):
    """Рецепты."""

    pub_date = models.DateTimeField(verbose_name='Дата создания',
                                    auto_now_add=True)

    name = models.CharField(max_length=50, unique=True,
                            verbose_name='Название рецепта',
                            help_text='Название рецепта')

    ingredients = models.ManyToManyField(Ingredient,
                                         through=RecipeIngredient,
                                         related_name='recipes',
                                         verbose_name='Ингредиенты',
                                         help_text='Необходимые ингредиенты')

    tags = models.ManyToManyField(Tag, verbose_name='Теги',
                                  help_text='Выберите теги',
                                  related_name='recipes')

    text = models.TextField(verbose_name='Текст рецепта',
                            help_text='Текст рецепта')

    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        default=1,
        validators=[
            MinValueValidator(1, message='Минимальное время 1 минута'),
        ],
        help_text='Время приготовления в минутах')

    image = models.ImageField(verbose_name='Картинка',
                              upload_to='recipes/images/')

    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                               verbose_name='Автор', related_name='recipes')

    class Meta:
        verbose_name = 'Рецепт',
        verbose_name_plural = 'Рецепты',
        ordering = ['-pub_date']
        constraints = [
            models.UniqueConstraint(fields=['name', 'author'],
                                    name='recipe_author_unique')]

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """Избранные рецепты пользователя."""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                             verbose_name='Пользователь',
                             related_name='favourites')

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепт',
                               related_name='in_favourites')

    class Meta:
        verbose_name = 'Избранный рецепт',
        verbose_name_plural = 'Избранные рецепты',
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favourites'
            )
        ]


class ShoppingCart(models.Model):
    """
    Модель для создания списка покупок из ингредиентов,
    необходимых для выбранных пользователем рецептов.
    """

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                             verbose_name='Пользователь',
                             related_name='shopping_cart')

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепт',
                               related_name='in_shopping_cart')

    class Meta:
        verbose_name = 'Рецепт в списке покупок',
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart'
            )
        ]
