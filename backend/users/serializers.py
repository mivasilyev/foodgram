import base64
import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from constants import FORBIDDEN_NAMES, MAX_LENGTH, USERNAME_PATTERN

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Сериализатор для обработки избображений."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


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

    def get_is_subscribed(self, obj):
        if self.context:
            user = self.context.get('request').user
            if user.is_authenticated:
                return obj in user.is_subscribed.all()
        return False
