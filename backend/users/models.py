from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя для проекта Foodgram.
    Авторизация по email.
    """

    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True,
        help_text='Введите ваш адрес электронной почты'
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=150,
        unique=True,
        help_text='Укажите уникальное имя пользователя'
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        help_text='Введите ваше имя'
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
        help_text='Введите вашу фамилию'
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=128,
        help_text='Введите надёжный пароль'
    )
    subscriptions = models.ManyToManyField(
        to='self',
        verbose_name='Подписки на авторов',
        related_name='подписчики',
        symmetrical=False,
        blank=True,
        help_text='Пользователи, на которых оформлена подписка'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']

    def __str__(self):
        return f'{self.username} ({self.email})'
