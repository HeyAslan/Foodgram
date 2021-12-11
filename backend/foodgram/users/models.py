from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    email = models.EmailField(unique=True)
    favourites = models.ManyToManyField(
        'recipes.Recipe',
        blank=True,
        related_name='is_favorited',
        verbose_name='Избранное'
    )
    shopping_cart = models.ManyToManyField(
        'recipes.Recipe',
        blank=True,
        related_name='is_in_shopping_cart',
        verbose_name='Список покупок'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
