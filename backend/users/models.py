from django.contrib.auth.models import AbstractUser
from django.db import models

from constants import DEFAULT_USER_AVATAR, MAX_LENGTH


class MyUser(AbstractUser):
    """Кастомная модель пользователя."""

    email = models.CharField(
        verbose_name='Электронная почта', max_length=MAX_LENGTH, unique=True
    )
    username = models.CharField(
        verbose_name='Ник', max_length=MAX_LENGTH, unique=True
    )
    first_name = models.CharField(verbose_name='Имя', max_length=MAX_LENGTH)
    last_name = models.CharField(verbose_name='Фамилия', max_length=MAX_LENGTH)
    is_subscribed = models.ManyToManyField(
        'self',
        through='Subscribe',
        verbose_name='Подписки',
        symmetrical=False,
        blank=True
    )
    avatar = models.ImageField(
        verbose_name='Аватар', upload_to='user_avatars', blank=True,
        default=DEFAULT_USER_AVATAR
    )
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name',]
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель подписки пользователей друг на друга."""

    user = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь'
    )
    subscribed = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписан на'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            # Запрещена повторная подписка.
            models.UniqueConstraint(
                fields=['user', 'subscribed'],
                name='unique_subscription'
            ),
            # Запрещена подписка на себя.
            models.CheckConstraint(
                check=~models.Q(user=models.F('subscribed')),
                name='self_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} на {self.subscribed}'
