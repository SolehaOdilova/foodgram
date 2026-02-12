from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

username_validator = UnicodeUsernameValidator()
# Константы
MAX_USERNAME_LENGTH = 150
MAX_EMAIL_LENGTH = 254
MAX_NAME_LENGTH = 150
MAX_PASSWORD_LENGTH = 128


class User(AbstractUser):
    """
    Кастомная модель пользователя для проекта Foodgram.
    Авторизация по email.
    """
    email = models.EmailField(
        verbose_name="Адрес электронной почты",
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        help_text="Введите ваш адрес электронной почты",
    )
    username = models.CharField(
        verbose_name="Имя пользователя",
        max_length=150,
        unique=True,
        help_text="Укажите уникальное имя пользователя",
        validators=[username_validator],
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=MAX_NAME_LENGTH,
        help_text="Введите ваше имя"
    )

    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=MAX_NAME_LENGTH,
        help_text="Введите вашу фамилию",
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, default="")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["username"]

    def __str__(self):
        return f"{self.username} ({self.email})"

    @property
    def followers_count(self):
        """Количество подписчиков.
        (людей, которые подписаны на этого пользователя)
        """
        return self.subscribers.count()

    @property
    def following_count(self):
        """Количество авторов, на которых подписан пользователь"""
        return self.subscriptions.count()

    @property
    def favorited_recipes(self):
        """Рецепты, добавленные пользователем в избранное."""
        from recipes.models import Recipe

        return Recipe.objects.filter(favorited__user=self)

    @property
    def shopping_cart_recipes(self):
        """Рецепты, добавленные пользователем в корзину."""
        from recipes.models import Recipe

        return Recipe.objects.filter(in_shopping_cart__user=self)


class Subscription(models.Model):
    """Модель подписки пользователя на другого пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="unique_user_author_subscription"
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="prevent_self_subscription",
            ),
        ]

    def __str__(self):
        return f"{self.user} → {self.author}"
