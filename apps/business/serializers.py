from rest_framework import serializers
from .models import Product, Order, Shop


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор товара. owner выставляется автоматически из request."""

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'owner_id', 'created_at']
        read_only_fields = ['id', 'owner_id', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор заказа.
    При создании принимает product (PrimaryKeyRelatedField).
    """
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )

    class Meta:
        model = Order
        fields = ['id', 'product', 'status', 'owner_id', 'created_at']
        read_only_fields = ['id', 'owner_id', 'status', 'created_at']


class ShopSerializer(serializers.ModelSerializer):
    """Сериализатор магазина."""

    class Meta:
        model = Shop
        fields = ['id', 'name', 'city', 'owner_id', 'created_at']
        read_only_fields = ['id', 'owner_id', 'created_at']
