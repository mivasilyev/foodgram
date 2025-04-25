import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from constants import FORBIDDEN_NAMES, MAX_LENGTH, USERNAME_PATTERN

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Доработанный сериализатор djoser для создания новых пользователей."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )

    def validate_username(self, value):
        if value in FORBIDDEN_NAMES:
            raise ValidationError(
                f'Имя пользователя {value} не разрешено.'
            )
        if not re.fullmatch(USERNAME_PATTERN, value):
            raise ValidationError(
                'Имя пользователя может содержать буквы, цифры и знаки '
                '@/./+/-/_.'
            )
        if len(value) > MAX_LENGTH:
            raise ValidationError(
                'В имени пользователя должно быть не более '
                f'{MAX_LENGTH} символов.'
            )
        return value


class CustomUserSerializer(UserSerializer):
    """Доработанный сериализатор djoser для пользователей."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, to_user):
        if self.context:
            user = self.context.get('request').user
            if user.is_authenticated:
                return to_user in user.is_subscribed.all()
        return False
