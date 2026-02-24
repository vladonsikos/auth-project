"""
Service Layer для бизнес-объектов: товары, заказы, магазины.

Вся логика фильтрации по владельцу и проверки прав на уровне объекта
вынесена сюда из views.
"""

from apps.users.models import User
from apps.access.permissions import has_permission
from .models import Product, Order, Shop


class ProductService:
    """Сервис управления товарами."""

    @staticmethod
    def get_list(user: User) -> list:
        """
        Возвращает список товаров согласно правам пользователя.
        read_all — все товары, read — только свои.

        Args:
            user: аутентифицированный пользователь

        Returns:
            QuerySet товаров
        """
        if has_permission(user, 'products', 'read_all'):
            return Product.objects.select_related('owner').all()
        return Product.objects.select_related('owner').filter(owner=user)

    @staticmethod
    def create(user: User, validated_data: dict) -> Product:
        """
        Создаёт товар от имени пользователя.

        Args:
            user:           владелец
            validated_data: данные из ProductSerializer

        Returns:
            Созданный объект Product
        """
        return Product.objects.create(owner=user, **validated_data)

    @staticmethod
    def can_read(user: User, product: Product) -> bool:
        """Проверяет право на чтение конкретного товара."""
        return (
            has_permission(user, 'products', 'read_all') or
            (has_permission(user, 'products', 'read') and product.owner_id == user.id)
        )

    @staticmethod
    def can_update(user: User, product: Product) -> bool:
        """Проверяет право на изменение конкретного товара."""
        return (
            has_permission(user, 'products', 'update_all') or
            (has_permission(user, 'products', 'update') and product.owner_id == user.id)
        )

    @staticmethod
    def can_delete(user: User, product: Product) -> bool:
        """Проверяет право на удаление конкретного товара."""
        return (
            has_permission(user, 'products', 'delete_all') or
            (has_permission(user, 'products', 'delete') and product.owner_id == user.id)
        )

    @staticmethod
    def update(product: Product, validated_data: dict) -> Product:
        """Обновляет поля товара."""
        for field, value in validated_data.items():
            setattr(product, field, value)
        product.save()
        return product


class OrderService:
    """Сервис управления заказами."""

    @staticmethod
    def get_list(user: User):
        """
        Возвращает заказы согласно правам пользователя.

        Args:
            user: аутентифицированный пользователь

        Returns:
            QuerySet заказов или None если нет прав
        """
        if has_permission(user, 'orders', 'read_all'):
            return Order.objects.select_related('owner', 'product').all()
        if has_permission(user, 'orders', 'read'):
            return Order.objects.select_related('owner', 'product').filter(owner=user)
        return None

    @staticmethod
    def create(user: User, validated_data: dict) -> Order:
        """
        Создаёт заказ от имени пользователя.

        Args:
            user:           владелец заказа
            validated_data: данные из OrderSerializer

        Returns:
            Созданный объект Order
        """
        return Order.objects.create(owner=user, **validated_data)


class ShopService:
    """Сервис управления магазинами."""

    @staticmethod
    def get_list():
        """Возвращает все магазины."""
        return Shop.objects.select_related('owner').all()

    @staticmethod
    def create(user: User, validated_data: dict) -> Shop:
        """
        Создаёт магазин от имени пользователя.

        Args:
            user:           владелец
            validated_data: данные из ShopSerializer

        Returns:
            Созданный объект Shop
        """
        return Shop.objects.create(owner=user, **validated_data)
