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

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название тега',
    )

    color = models.CharField(
        max_length=50,
        choices=COLOR_CHOICES,
        verbose_name='Цвет',
    )

    slug = models.SlugField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Слаг',
    )

    class Meta:
        verbose_name = 'Тег',
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ингредиенты для рецептов."""

    name = models.CharField(
        max_length=150,
        db_index=True,
        verbose_name='Название ингредиента',
    )

    measurement_unit = models.CharField(
        max_length=150,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class RecipeIngredient(models.Model):
    """Необходимое количество ингредиентов."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
        verbose_name='Рецепт',
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Ингредиент',
    )

    amount = models.FloatField(
        verbose_name='Количество ингредиента',
        validators=(MinValueValidator(
            1, message='Минимальное количество ингредиентов 1'),))

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipe_ingredient_unique',
            ),
        ]

    def __str__(self):
        return (
            f'{self.recipe.name} - '
            f'{self.ingredient.name} '
            f'({self.amount})')


class Recipe(models.Model):
    """Рецепты."""

    pub_date = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
    )

    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Название рецепта',
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through=RecipeIngredient,
        related_name='recipes',
        verbose_name='Ингредиенты',
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
    )

    text = models.TextField(
        verbose_name='Текст рецепта',
    )

    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(
                1,
                message='Минимальное время 1 минута'
            ),
        ]
    )

    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/images/',
    )

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']
        constraints = [
            models.UniqueConstraint(fields=['name', 'author'],
                                    name='recipe_author_unique')]

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """Избранные рецепты пользователя."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Избранные рецепты',
        related_name='favorites',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Избранные у пользователей',
        related_name='in_favorites',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorites',
            ),
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное'


class ShoppingCart(models.Model):
    """
    Модель для создания списка покупок из ингредиентов,
    необходимых для выбранных пользователем рецептов.
    """

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Список покупок',
        related_name='shopping_cart',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='В списке покупок',
        related_name='shopping_cart',
    )

    class Meta:
        default_related_name = 'shopping'
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart',
            ),
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в список покупок'
