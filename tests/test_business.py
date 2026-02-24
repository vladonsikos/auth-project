"""
Тесты бизнес-объектов: товары, заказы, магазины.
Проверяет RBAC-логику: read/read_all, create, update/update_all, delete/delete_all.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.users.models import User, Session
from apps.access.models import Role, UserRole, BusinessElement, AccessRule
from apps.business.models import Product, Order, Shop
from apps.users.utils import hash_password, generate_token


# ─── Вспомогательные функции ─────────────────────────────────────────────────

def create_role(name):
    """Создаёт или возвращает роль."""
    return Role.objects.get_or_create(name=name)[0]


def create_user(email, role_name='user'):
    """Создаёт пользователя с указанной ролью."""
    role = create_role(role_name)
    user = User.objects.create(
        first_name='Test', last_name='User',
        email=email, password_hash=hash_password('pass1234'),
    )
    UserRole.objects.create(user=user, role=role)
    return user


def auth_client(user):
    """Возвращает APIClient с токеном."""
    token, expires_at = generate_token(user.id)
    Session.objects.create(user=user, token=token, expires_at=expires_at)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


def grant(role, element_name, **permissions):
    """
    Создаёт или обновляет AccessRule для роли и бизнес-объекта.

    Args:
        role:         объект Role
        element_name: строка, например 'products'
        **permissions: read=True, create=True, ...
    """
    element, _ = BusinessElement.objects.get_or_create(name=element_name)
    rule, _ = AccessRule.objects.get_or_create(role=role, element=element)
    for field, value in permissions.items():
        setattr(rule, field, value)
    rule.save()
    return rule


# ─── Тесты товаров ───────────────────────────────────────────────────────────

class ProductListTests(TestCase):
    """Тесты GET/POST /api/business/products/"""

    def setUp(self):
        # Пользователь с read_all + create
        self.manager_role = create_role('manager')
        self.manager = create_user('manager@test.com', 'manager')
        grant(self.manager_role, 'products', read_all=True, create=True)
        self.manager_client = auth_client(self.manager)

        # Пользователь без прав
        self.guest_role = create_role('guest')
        self.guest = create_user('guest@test.com', 'guest')
        self.guest_client = auth_client(self.guest)

        # Несколько товаров
        Product.objects.create(name='Laptop', price=80000, owner=self.manager)
        Product.objects.create(name='Phone', price=40000, owner=self.manager)

    def test_list_products_with_read_all(self):
        """Менеджер с read_all видит все товары."""
        response = self.manager_client.get('/api/business/products/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_list_products_unauthenticated(self):
        """Неаутентифицированный запрос возвращает 401."""
        response = APIClient().get('/api/business/products/')
        self.assertEqual(response.status_code, 401)

    def test_create_product_success(self):
        """Менеджер создаёт товар."""
        response = self.manager_client.post('/api/business/products/', {
            'name': 'Tablet', 'price': 25000,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Product.objects.filter(name='Tablet').exists())

    def test_create_product_no_permission(self):
        """Гость без прав получает 403."""
        response = self.guest_client.post('/api/business/products/', {
            'name': 'SomeThing', 'price': 100,
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_create_product_missing_fields(self):
        """Создание товара без обязательных полей возвращает 400."""
        response = self.manager_client.post('/api/business/products/', {}, format='json')
        self.assertEqual(response.status_code, 400)


class ProductDetailTests(TestCase):
    """Тесты GET/PATCH/DELETE /api/business/products/<pk>/"""

    def setUp(self):
        # Владелец с правами на свои объекты
        self.user_role = create_role('user')
        self.owner = create_user('owner@test.com', 'user')
        grant(self.user_role, 'products',
              read=True, update=True, delete=True, create=True)
        self.owner_client = auth_client(self.owner)

        # Другой пользователь
        self.other = create_user('other@test.com', 'user')
        self.other_client = auth_client(self.other)

        # Менеджер с правами на всё
        self.mgr_role = create_role('manager')
        self.manager = create_user('mgr@test.com', 'manager')
        grant(self.mgr_role, 'products',
              read_all=True, update_all=True, delete_all=True)
        self.manager_client = auth_client(self.manager)

        self.product = Product.objects.create(
            name='MyProduct', price=5000, owner=self.owner
        )

    def test_owner_can_read_own_product(self):
        """Владелец читает свой товар."""
        response = self.owner_client.get(f'/api/business/products/{self.product.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'MyProduct')

    def test_other_user_cannot_read_product(self):
        """Другой пользователь получает 403."""
        response = self.other_client.get(f'/api/business/products/{self.product.id}/')
        self.assertEqual(response.status_code, 403)

    def test_manager_can_read_any_product(self):
        """Менеджер с read_all читает чужой товар."""
        response = self.manager_client.get(f'/api/business/products/{self.product.id}/')
        self.assertEqual(response.status_code, 200)

    def test_product_not_found(self):
        """Несуществующий товар возвращает 404."""
        response = self.owner_client.get('/api/business/products/99999/')
        self.assertEqual(response.status_code, 404)

    def test_owner_can_update_own_product(self):
        """Владелец обновляет свой товар."""
        response = self.owner_client.patch(
            f'/api/business/products/{self.product.id}/',
            {'name': 'UpdatedProduct'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'UpdatedProduct')

    def test_other_user_cannot_update_product(self):
        """Чужой пользователь не может обновить товар."""
        response = self.other_client.patch(
            f'/api/business/products/{self.product.id}/',
            {'name': 'Hacked'}, format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_manager_can_update_any_product(self):
        """Менеджер с update_all обновляет чужой товар."""
        response = self.manager_client.patch(
            f'/api/business/products/{self.product.id}/',
            {'price': 9999}, format='json',
        )
        self.assertEqual(response.status_code, 200)

    def test_owner_can_delete_own_product(self):
        """Владелец удаляет свой товар."""
        response = self.owner_client.delete(f'/api/business/products/{self.product.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_other_user_cannot_delete_product(self):
        """Чужой пользователь не может удалить товар."""
        response = self.other_client.delete(f'/api/business/products/{self.product.id}/')
        self.assertEqual(response.status_code, 403)

    def test_manager_can_delete_any_product(self):
        """Менеджер с delete_all удаляет чужой товар."""
        response = self.manager_client.delete(f'/api/business/products/{self.product.id}/')
        self.assertEqual(response.status_code, 204)


# ─── Тесты заказов ───────────────────────────────────────────────────────────

class OrderListTests(TestCase):
    """Тесты GET/POST /api/business/orders/"""

    def setUp(self):
        self.user_role = create_role('user')
        self.user1 = create_user('u1@test.com', 'user')
        self.user2 = create_user('u2@test.com', 'user')
        grant(self.user_role, 'orders', read=True, create=True)
        self.client1 = auth_client(self.user1)
        self.client2 = auth_client(self.user2)

        self.mgr_role = create_role('manager')
        self.manager = create_user('mgr@test.com', 'manager')
        grant(self.mgr_role, 'orders', read_all=True)
        self.manager_client = auth_client(self.manager)

        self.product = Product.objects.create(
            name='Item', price=100, owner=self.user1
        )
        Order.objects.create(product=self.product, owner=self.user1)
        Order.objects.create(product=self.product, owner=self.user2)

    def test_user_sees_only_own_orders(self):
        """Пользователь с read видит только свои заказы."""
        response = self.client1.get('/api/business/orders/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_manager_sees_all_orders(self):
        """Менеджер с read_all видит все заказы."""
        response = self.manager_client.get('/api/business/orders/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_create_order_success(self):
        """Пользователь создаёт заказ."""
        response = self.client1.post('/api/business/orders/', {
            'product': self.product.id,
            'status': 'pending',
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_create_order_invalid_product(self):
        """Заказ с несуществующим product_id возвращает 400."""
        response = self.client1.post('/api/business/orders/', {
            'product': 99999,
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_cannot_list_orders(self):
        """Без токена — 401."""
        response = APIClient().get('/api/business/orders/')
        self.assertEqual(response.status_code, 401)

    def test_no_permission_returns_403(self):
        """Пользователь без прав на orders получает 403."""
        no_perm_role = create_role('noperm')
        no_perm_user = create_user('noperm@test.com', 'noperm')
        # Не выдаём никаких прав на orders
        client = auth_client(no_perm_user)
        response = client.get('/api/business/orders/')
        self.assertEqual(response.status_code, 403)


# ─── Тесты магазинов ─────────────────────────────────────────────────────────

class ShopListTests(TestCase):
    """Тесты GET/POST /api/business/shops/"""

    def setUp(self):
        self.user_role = create_role('user')
        self.user = create_user('user@test.com', 'user')
        # У роли user нет прав на shops

        self.mgr_role = create_role('manager')
        self.manager = create_user('mgr@test.com', 'manager')
        grant(self.mgr_role, 'shops', read_all=True, create=True)
        self.manager_client = auth_client(self.manager)
        self.user_client = auth_client(self.user)

        Shop.objects.create(name='TechMart', city='Москва', owner=self.manager)

    def test_manager_can_list_shops(self):
        """Менеджер с read_all видит все магазины."""
        response = self.manager_client.get('/api/business/shops/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_user_without_permission_gets_403(self):
        """Пользователь без прав на shops получает 403."""
        response = self.user_client.get('/api/business/shops/')
        self.assertEqual(response.status_code, 403)

    def test_manager_can_create_shop(self):
        """Менеджер создаёт магазин."""
        response = self.manager_client.post('/api/business/shops/', {
            'name': 'NewShop', 'city': 'Казань',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Shop.objects.filter(name='NewShop').exists())

    def test_create_shop_missing_fields(self):
        """Создание магазина без обязательных полей возвращает 400."""
        response = self.manager_client.post('/api/business/shops/', {}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_cannot_list_shops(self):
        """Без токена — 403 (permission_required проверяет auth первым)."""
        response = APIClient().get('/api/business/shops/')
        self.assertEqual(response.status_code, 401)
