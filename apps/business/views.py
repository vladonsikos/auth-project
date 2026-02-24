"""
Views для бизнес-объектов: товары, заказы, магазины.
Используют реальные модели в БД (вместо mock-данных).
Права проверяются через permission_required и ProductService.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404

from apps.access.permissions import permission_required, login_required
from .models import Product, Order, Shop
from .serializers import ProductSerializer, OrderSerializer, ShopSerializer
from .services import ProductService, OrderService, ShopService


class ProductListView(APIView):
    """GET/POST /api/business/products/"""

    @login_required
    def get(self, request):
        """
        Возвращает список товаров.
        read_all — все товары, read — только свои.
        """
        products = ProductService.get_list(request.current_user)
        return Response(ProductSerializer(products, many=True).data)

    @permission_required('products', 'create')
    def post(self, request):
        """
        Создаёт товар. Владелец — текущий пользователь.

        Body: name, price
        Returns: 201 или 400
        """
        serializer = ProductSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        product = ProductService.create(request.current_user, serializer.validated_data)
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    """GET/PATCH/DELETE /api/business/products/<pk>/"""

    @login_required
    def get(self, request, pk):
        """
        Возвращает товар по ID.
        Проверяет право read или read_all.
        """
        product = get_object_or_404(Product, pk=pk)
        if not ProductService.can_read(request.current_user, product):
            return Response({'detail': 'Доступ запрещён.'}, status=status.HTTP_403_FORBIDDEN)
        return Response(ProductSerializer(product).data)

    @login_required
    def patch(self, request, pk):
        """
        Обновляет товар. Проверяет право update или update_all.

        Body: name?, price?
        """
        product = get_object_or_404(Product, pk=pk)
        if not ProductService.can_update(request.current_user, product):
            return Response({'detail': 'Доступ запрещён.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        product = ProductService.update(product, serializer.validated_data)
        return Response(ProductSerializer(product).data)

    @login_required
    def delete(self, request, pk):
        """Удаляет товар. Проверяет право delete или delete_all."""
        product = get_object_or_404(Product, pk=pk)
        if not ProductService.can_delete(request.current_user, product):
            return Response({'detail': 'Доступ запрещён.'}, status=status.HTTP_403_FORBIDDEN)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderListView(APIView):
    """GET/POST /api/business/orders/"""

    @login_required
    def get(self, request):
        """
        Возвращает заказы согласно правам.
        read_all — все, read — только свои.
        """
        orders = OrderService.get_list(request.current_user)
        if orders is None:
            return Response({'detail': 'Доступ запрещён.'}, status=status.HTTP_403_FORBIDDEN)
        return Response(OrderSerializer(orders, many=True).data)

    @permission_required('orders', 'create')
    def post(self, request):
        """
        Создаёт заказ.

        Body: product_id
        Returns: 201 или 400
        """
        serializer = OrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        order = OrderService.create(request.current_user, serializer.validated_data)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class ShopListView(APIView):
    """GET/POST /api/business/shops/"""

    @permission_required('shops', 'read_all')
    def get(self, request):
        """Возвращает все магазины."""
        shops = ShopService.get_list()
        return Response(ShopSerializer(shops, many=True).data)

    @permission_required('shops', 'create')
    def post(self, request):
        """
        Создаёт магазин.

        Body: name, city
        Returns: 201 или 400
        """
        serializer = ShopSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        shop = ShopService.create(request.current_user, serializer.validated_data)
        return Response(ShopSerializer(shop).data, status=status.HTTP_201_CREATED)
