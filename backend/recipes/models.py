from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from foodgram.settings import MIN_COOK_TIME

User = get_user_model()


class Ingredient(models.Model):
    """Ingredient model."""
    name = models.CharField(
        blank=False,
        max_length=200,
        verbose_name='Ingredients Name',
        db_index=True
    )
    measurement_unit = models.CharField(
        blank=False,
        max_length=150,
        verbose_name='Measurement Unit',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """Tag model."""
    name = models.CharField(
        unique=True,
        max_length=50,
        verbose_name='Tag name',
    )
    color = models.CharField(
        unique=True,
        max_length=16,
        verbose_name='Color (Hex-Code)',
    )
    slug = models.SlugField(
        verbose_name='Unique slug',
        unique=True,
        max_length=200
    )

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Recipe model."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Author',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientsAmount',
        related_name='recipes',
        verbose_name='Ingredients',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Tags'
    )
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Title',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Image',
    )
    text = models.CharField(
        max_length=500,
        verbose_name='Text',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Cooking Time',
        validators=[
            MinValueValidator(
                MIN_COOK_TIME,
                message=f'Minimal cooking time is {MIN_COOK_TIME}!'
            )
        ],
        help_text='in minutes',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date',
    )

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class Favourite(models.Model):
    """Favourite model."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='who_favourited',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favourites',
    )

    class Meta:
        verbose_name = 'Favourite'
        verbose_name_plural = 'Favourites'
        ordering = ('id',)
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favourites'
            ),
        )


class IngredientsAmount(models.Model):
    """Ingredients list model."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Recipe',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ingredient',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='quantity',
        default=1,
        validators=[MinValueValidator(1, 'the weight cannot be less than 1')])

    class Meta:
        verbose_name = 'Ingredients amount'
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'],
                                    name='unique_recipe_ingredient')
        ]

    def __str__(self):
        return f'{self.ingredient}: {self.amount}'


class ShoppingCart(models.Model):
    """Shopping Cart model."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Recipe',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='User',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart'
            )
        ]
        verbose_name = 'Shopping Cart'
        verbose_name_plural = 'Shopping Carts'
