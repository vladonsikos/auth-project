from django.db import models
from apps.users.models import User


class Product(models.Model):
    """
    Товар в системе.

    Поля:
        name     — название товара
        price    — цена (целое число, копейки или рубли — на усмотрение)
        owner    — пользователь, создавший товар
        created_at — дата создания
    """

    name = models.CharField(max_length=200, verbose_name='Название')
    price = models.PositiveIntegerField(default=0, verbose_name='Цена')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'products'
        verbose_name = 'Товар'

    def __str__(self):
        return f'{self.name} ({self.price})'


class Order(models.Model):
    """
    Заказ пользователя.

    Поля:
        product  — товар в заказе
        status   — статус: pending / shipped / delivered
        owner    — пользователь, создавший заказ
        created_at — дата создания
    """

    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders'
        verbose_name = 'Заказ'

    def __str__(self):
        return f'Заказ #{self.id} — {self.status}'


class Shop(models.Model):
    """
    Магазин.

    Поля:
        name   — название магазина
        city   — город
        owner  — пользователь, создавший магазин
        created_at — дата создания
    """

    name = models.CharField(max_length=200, verbose_name='Название')
    city = models.CharField(max_length=100, verbose_name='Город')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shops')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shops'
        verbose_name = 'Магазин'

    def __str__(self):
        return f'{self.name} ({self.city})'
