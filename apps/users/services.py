"""
Service Layer для аутентификации и управления пользователями.

Вся бизнес-логика вынесена сюда из views, чтобы:
- views оставались тонкими (только HTTP-слой)
- логику можно было тестировать независимо от HTTP
"""

from django.db import transaction
from .models import User, Session
from .utils import hash_password, check_password, generate_token
from apps.access.models import Role, UserRole


class AuthService:
    """Сервис регистрации, входа и выхода из системы."""

    @staticmethod
    @transaction.atomic
    def register(validated_data: dict) -> User:
        """
        Создаёт нового пользователя и назначает ему роль 'user' по умолчанию.

        Args:
            validated_data: провалидированные данные из RegisterSerializer

        Returns:
            Созданный объект User
        """
        user = User.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            patronymic=validated_data.get('patronymic', ''),
            email=validated_data['email'],
            password_hash=hash_password(validated_data['password']),
        )
        default_role = Role.objects.filter(name='user').first()
        if default_role:
            UserRole.objects.create(user=user, role=default_role)
        return user

    @staticmethod
    def login(email: str, password: str) -> dict | None:
        """
        Проверяет учётные данные и создаёт сессию.

        Args:
            email:    email пользователя
            password: пароль в открытом виде

        Returns:
            Словарь {'token': ..., 'expires_at': ..., 'user': ...}
            или None если учётные данные неверны
        """
        user = User.objects.filter(email=email, is_active=True).first()
        if not user or not check_password(password, user.password_hash):
            return None

        token, expires_at = generate_token(user.id)
        Session.objects.create(user=user, token=token, expires_at=expires_at)
        return {'token': token, 'expires_at': expires_at, 'user': user}

    @staticmethod
    def logout(token: str) -> None:
        """
        Деактивирует сессию по токену.

        Args:
            token: JWT-токен из заголовка Authorization
        """
        Session.objects.filter(token=token).update(is_active=False)

    @staticmethod
    def update_profile(user: User, validated_data: dict) -> User:
        """
        Обновляет поля профиля пользователя.

        Args:
            user:           объект User
            validated_data: провалидированные данные из UpdateUserSerializer

        Returns:
            Обновлённый объект User
        """
        for field, value in validated_data.items():
            setattr(user, field, value)
        user.save()
        return user

    @staticmethod
    @transaction.atomic
    def delete_account(user: User) -> None:
        """
        Мягко удаляет аккаунт: деактивирует все сессии и ставит is_active=False.

        Args:
            user: объект User
        """
        Session.objects.filter(user=user).update(is_active=False)
        user.is_active = False
        user.save()
