"""
Тесты аутентификации: регистрация, вход, выход, профиль, удаление аккаунта.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User, Session
from apps.access.models import Role, UserRole
from apps.users.utils import hash_password, generate_token


def create_role(name='user'):
    """Вспомогательная функция: создаёт роль."""
    return Role.objects.get_or_create(name=name)[0]


def create_user(email='test@example.com', password='pass1234', role_name='user'):
    """Вспомогательная функция: создаёт пользователя с ролью."""
    role = create_role(role_name)
    user = User.objects.create(
        first_name='Test', last_name='User',
        email=email, password_hash=hash_password(password),
    )
    UserRole.objects.create(user=user, role=role)
    return user


def auth_client(user):
    """Вспомогательная функция: возвращает APIClient с токеном."""
    token, expires_at = generate_token(user.id)
    Session.objects.create(user=user, token=token, expires_at=expires_at)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client, token


class RegisterTests(TestCase):
    """Тесты регистрации."""

    def setUp(self):
        self.client = APIClient()
        create_role('user')

    def test_register_success(self):
        """Успешная регистрация создаёт пользователя и возвращает 201."""
        response = self.client.post('/api/auth/register/', {
            'first_name': 'Ivan', 'last_name': 'Ivanov',
            'email': 'ivan@test.com', 'password': 'pass1234',
            'password_confirm': 'pass1234',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email='ivan@test.com').exists())

    def test_register_duplicate_email(self):
        """Повторная регистрация с тем же email возвращает 400."""
        create_user('dup@test.com')
        response = self.client.post('/api/auth/register/', {
            'first_name': 'A', 'last_name': 'B',
            'email': 'dup@test.com', 'password': 'pass1234',
            'password_confirm': 'pass1234',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register_password_mismatch(self):
        """Несовпадающие пароли возвращают 400."""
        response = self.client.post('/api/auth/register/', {
            'first_name': 'A', 'last_name': 'B',
            'email': 'new@test.com', 'password': 'pass1234',
            'password_confirm': 'wrong',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register_missing_fields(self):
        """Отсутствие обязательных полей возвращает 400."""
        response = self.client.post('/api/auth/register/', {
            'email': 'x@test.com',
        }, format='json')
        self.assertEqual(response.status_code, 400)


class LoginTests(TestCase):
    """Тесты входа в систему."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user('login@test.com', 'pass1234')

    def test_login_success(self):
        """Успешный вход возвращает токен."""
        response = self.client.post('/api/auth/login/', {
            'email': 'login@test.com', 'password': 'pass1234',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)

    def test_login_wrong_password(self):
        """Неверный пароль возвращает 401."""
        response = self.client.post('/api/auth/login/', {
            'email': 'login@test.com', 'password': 'wrongpass',
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_login_unknown_email(self):
        """Неизвестный email возвращает 401."""
        response = self.client.post('/api/auth/login/', {
            'email': 'nobody@test.com', 'password': 'pass1234',
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_login_inactive_user(self):
        """Деактивированный пользователь не может войти."""
        self.user.is_active = False
        self.user.save()
        response = self.client.post('/api/auth/login/', {
            'email': 'login@test.com', 'password': 'pass1234',
        }, format='json')
        self.assertEqual(response.status_code, 401)


class LogoutTests(TestCase):
    """Тесты выхода из системы."""

    def setUp(self):
        user = create_user('logout@test.com')
        self.client, self.token = auth_client(user)

    def test_logout_success(self):
        """Успешный выход деактивирует сессию."""
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Session.objects.filter(token=self.token, is_active=True).exists())

    def test_logout_without_token(self):
        """Выход без токена возвращает 401."""
        client = APIClient()
        response = client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 401)


class ProfileTests(TestCase):
    """Тесты профиля пользователя."""

    def setUp(self):
        self.user = create_user('profile@test.com')
        self.client, _ = auth_client(self.user)

    def test_get_profile(self):
        """GET профиля возвращает данные текущего пользователя."""
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'profile@test.com')

    def test_update_profile(self):
        """PATCH профиля обновляет имя."""
        response = self.client.patch('/api/auth/profile/', {
            'first_name': 'Updated',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['first_name'], 'Updated')

    def test_delete_account(self):
        """DELETE аккаунта деактивирует пользователя."""
        response = self.client.delete('/api/auth/profile/delete/')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_profile_requires_auth(self):
        """Профиль без токена возвращает 401."""
        response = APIClient().get('/api/auth/profile/')
        self.assertEqual(response.status_code, 401)
