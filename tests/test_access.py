"""
Тесты RBAC: управление ролями, правилами доступа и назначением ролей.
Все эндпоинты /api/access/ доступны только пользователям с ролью admin.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.users.models import User, Session
from apps.access.models import Role, UserRole, BusinessElement, AccessRule
from apps.users.utils import hash_password, generate_token


# ─── Вспомогательные функции ─────────────────────────────────────────────────

def create_role(name='user', description=''):
    """Создаёт роль с указанным именем."""
    return Role.objects.get_or_create(name=name, defaults={'description': description})[0]


def create_user(email='test@example.com', password='pass1234', role_name='user'):
    """Создаёт пользователя и назначает ему роль."""
    role = create_role(role_name)
    user = User.objects.create(
        first_name='Test', last_name='User',
        email=email, password_hash=hash_password(password),
    )
    UserRole.objects.create(user=user, role=role)
    return user


def auth_client(user):
    """Возвращает APIClient с Bearer-токеном для указанного пользователя."""
    token, expires_at = generate_token(user.id)
    Session.objects.create(user=user, token=token, expires_at=expires_at)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


# ─── Тесты ролей ─────────────────────────────────────────────────────────────

class RoleListTests(TestCase):
    """Тесты GET/POST /api/access/roles/"""

    def setUp(self):
        self.admin = create_user('admin@test.com', role_name='admin')
        self.user = create_user('user@test.com', role_name='user')
        self.admin_client = auth_client(self.admin)
        self.user_client = auth_client(self.user)

    def test_admin_can_list_roles(self):
        """Администратор получает список ролей."""
        response = self.admin_client.get('/api/access/roles/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertIsInstance(response.data['results'], list)

    def test_non_admin_cannot_list_roles(self):
        """Обычный пользователь получает 403."""
        response = self.user_client.get('/api/access/roles/')
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_list_roles(self):
        """Неаутентифицированный запрос получает 401."""
        response = APIClient().get('/api/access/roles/')
        self.assertEqual(response.status_code, 401)

    def test_admin_can_create_role(self):
        """Администратор создаёт новую роль."""
        response = self.admin_client.post('/api/access/roles/', {
            'name': 'moderator', 'description': 'Модератор',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Role.objects.filter(name='moderator').exists())

    def test_create_role_missing_name(self):
        """Создание роли без имени возвращает 400."""
        response = self.admin_client.post('/api/access/roles/', {
            'description': 'Без имени',
        }, format='json')
        self.assertEqual(response.status_code, 400)


class RoleDetailTests(TestCase):
    """Тесты GET/PATCH/DELETE /api/access/roles/<id>/"""

    def setUp(self):
        self.admin = create_user('admin@test.com', role_name='admin')
        self.admin_client = auth_client(self.admin)
        self.role = Role.objects.create(name='testrole', description='Тестовая роль')

    def test_get_role(self):
        """Администратор получает роль по ID."""
        response = self.admin_client.get(f'/api/access/roles/{self.role.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'testrole')

    def test_get_role_not_found(self):
        """Запрос несуществующей роли возвращает 404."""
        response = self.admin_client.get('/api/access/roles/99999/')
        self.assertEqual(response.status_code, 404)

    def test_patch_role(self):
        """Администратор обновляет описание роли."""
        response = self.admin_client.patch(f'/api/access/roles/{self.role.id}/', {
            'description': 'Обновлённое описание',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.role.refresh_from_db()
        self.assertEqual(self.role.description, 'Обновлённое описание')

    def test_delete_role(self):
        """Администратор удаляет роль."""
        role_id = self.role.id
        response = self.admin_client.delete(f'/api/access/roles/{role_id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Role.objects.filter(id=role_id).exists())


# ─── Тесты бизнес-объектов ───────────────────────────────────────────────────

class BusinessElementTests(TestCase):
    """Тесты GET/POST /api/access/elements/"""

    def setUp(self):
        self.admin = create_user('admin@test.com', role_name='admin')
        self.admin_client = auth_client(self.admin)

    def test_list_elements(self):
        """Администратор получает список бизнес-объектов."""
        BusinessElement.objects.create(name='products', description='Товары')
        response = self.admin_client.get('/api/access/elements/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_element(self):
        """Администратор создаёт новый бизнес-объект."""
        response = self.admin_client.post('/api/access/elements/', {
            'name': 'invoices', 'description': 'Счета',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(BusinessElement.objects.filter(name='invoices').exists())

    def test_non_admin_cannot_create_element(self):
        """Обычный пользователь получает 403."""
        user_client = auth_client(create_user('u@test.com', role_name='user'))
        response = user_client.post('/api/access/elements/', {
            'name': 'invoices',
        }, format='json')
        self.assertEqual(response.status_code, 403)


# ─── Тесты правил доступа ────────────────────────────────────────────────────

class AccessRuleTests(TestCase):
    """Тесты GET/POST/PATCH/DELETE /api/access/rules/"""

    def setUp(self):
        self.admin = create_user('admin@test.com', role_name='admin')
        self.admin_client = auth_client(self.admin)
        self.role = Role.objects.create(name='manager', description='Менеджер')
        self.element = BusinessElement.objects.create(name='products', description='Товары')
        self.rule = AccessRule.objects.create(
            role=self.role, element=self.element,
            read=True, read_all=True, create=True,
        )

    def test_list_rules(self):
        """Администратор получает список правил."""
        response = self.admin_client.get('/api/access/rules/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_rule(self):
        """Администратор получает правило по ID."""
        response = self.admin_client.get(f'/api/access/rules/{self.rule.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['read'])

    def test_get_rule_not_found(self):
        """Несуществующее правило возвращает 404."""
        response = self.admin_client.get('/api/access/rules/99999/')
        self.assertEqual(response.status_code, 404)

    def test_patch_rule(self):
        """Администратор обновляет права в правиле."""
        response = self.admin_client.patch(f'/api/access/rules/{self.rule.id}/', {
            'create': False,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.rule.refresh_from_db()
        self.assertFalse(self.rule.create)

    def test_delete_rule(self):
        """Администратор удаляет правило."""
        rule_id = self.rule.id
        response = self.admin_client.delete(f'/api/access/rules/{rule_id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(AccessRule.objects.filter(id=rule_id).exists())

    def test_create_rule(self):
        """Администратор создаёт новое правило доступа."""
        new_role = Role.objects.create(name='viewer')
        response = self.admin_client.post('/api/access/rules/', {
            'role': new_role.id,
            'element': self.element.id,
            'read': True, 'read_all': False, 'create': False,
            'update': False, 'update_all': False,
            'delete': False, 'delete_all': False,
        }, format='json')
        self.assertEqual(response.status_code, 201)


# ─── Тесты назначения ролей ──────────────────────────────────────────────────

class UserRoleTests(TestCase):
    """Тесты GET/POST/DELETE /api/access/user-roles/"""

    def setUp(self):
        self.admin = create_user('admin@test.com', role_name='admin')
        self.admin_client = auth_client(self.admin)
        self.target_user = User.objects.create(
            first_name='Target', last_name='User',
            email='target@test.com',
            password_hash=hash_password('pass1234'),
        )
        self.extra_role = Role.objects.create(name='manager', description='Менеджер')

    def test_list_user_roles(self):
        """Администратор получает список назначений ролей."""
        response = self.admin_client.get('/api/access/user-roles/')
        self.assertEqual(response.status_code, 200)

    def test_assign_role(self):
        """Администратор назначает роль пользователю."""
        response = self.admin_client.post('/api/access/user-roles/', {
            'user': self.target_user.id,
            'role': self.extra_role.id,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            UserRole.objects.filter(user=self.target_user, role=self.extra_role).exists()
        )

    def test_revoke_role(self):
        """Администратор отзывает роль у пользователя."""
        user_role = UserRole.objects.create(user=self.target_user, role=self.extra_role)
        response = self.admin_client.delete(f'/api/access/user-roles/{user_role.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(UserRole.objects.filter(id=user_role.id).exists())

    def test_non_admin_cannot_assign_role(self):
        """Обычный пользователь не может назначить роль."""
        user_client = auth_client(create_user('regular@test.com', role_name='user'))
        response = user_client.post('/api/access/user-roles/', {
            'user': self.target_user.id,
            'role': self.extra_role.id,
        }, format='json')
        self.assertEqual(response.status_code, 403)
