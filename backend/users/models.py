from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    """Кастомная модель пользователя."""

    email = models.CharField(
        verbose_name='Электронная почта', max_length=254, unique=True
    )
    username = models.CharField(
        verbose_name='Ник', max_length=150, unique=True
    )
    first_name = models.CharField(verbose_name='Имя', max_length=150)
    last_name = models.CharField(verbose_name='Фамилия', max_length=150)
    is_subscribed = models.BooleanField(null=True, default=0)
    avatar = models.ImageField(
        verbose_name='Аватар', upload_to='user_avatars', blank=True
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    @property
    def is_admin(self):
        return self.is_staff


class Follow(models.Model):
    """Модель подписки пользователей друг на друга."""

    user = models.ForeignKey(
        MyUser, on_delete=models.CASCADE,
        related_name='follower', verbose_name='Пользователь')
    following = models.ForeignKey(
        MyUser, on_delete=models.CASCADE,
        related_name='following', verbose_name='Подписан'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            # Запрещена повторная подписка.
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_subscription'
            ),
            # Запрещена подписка на себя.
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='self_subscription'
            )
        ]
