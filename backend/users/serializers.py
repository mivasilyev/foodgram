import base64
import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from constants import FORBIDDEN_NAMES, USERNAME_PATTERN, MAX_USERNAME_LENGTH

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор djoser для создания новых пользователей с доп. полями."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password')

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
        if len(value) > MAX_USERNAME_LENGTH:
            raise ValidationError(
                'В имени пользователя должно быть не более '
                f'{MAX_USERNAME_LENGTH} символов.'
            )
        return value


class CustomUserSerializer(UserSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )


class Base64ImageField(serializers.ImageField):
    """Сериализатор для обработки избображений."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)
