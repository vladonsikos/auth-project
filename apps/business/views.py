"""
Mock-views для демонстрации системы авторизации.
Реальных таблиц в БД не создаётся — данные хранятся в памяти.
Каждый эндпоинт проверяет права через has_permission().
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.access.permissions import permission_required, login_required


# ─── Фиктивные данные ────────────────────────────────────────────────────────

MOCK_PRODUCTS = [
    {'id': 1, 'name': 'Ноутбук ProBook', 'price': 89990, 'owner_id': 2},
    {'id': 2, 'name': 'Смартфон Galaxy', 'price': 45000, 'owner_id': 3},
    {'id': 3, 'name': 'Наушники SoundPro', 'price': 7500, 'owner_id': 2},
]

MOCK_ORDERS = [
    {'id': 1, 'product_id': 1, 'status': 'pending', 'owner_id': 3},
    {'id': 2, 'product_id': 2, 'status': 'shipped', 'owner_id': 2},
    {'id': 3, 'product_id': 3, 'status': 'delivered', 'owner_id': 3},
]

MOCK_SHOPS = [
    {'id': 1, 'name': 'TechMart', 'city': 'Москва', 'owner_id': 2},
    {'id': 2, 'name': 'GadgetWorld', 'city': 'Санкт-Петербург', 'owner_id': 3},
]


# ─── Товары ──────────────────────────────────────────────────────────────────

class ProductListView(APIView):
    """
    GET  /api/business/products/  — список товаров (требует read_all или read)
    POST /api/business/products/  — создать товар (требует create)
    """

    @permission_required('products', 'read_all')
    def get(self, request):
        return Response({'products': MOCK_PRODUCTS})

    @permission_required('products', 'create')
    def post(self, request):
        new_product = {
            'id': len(MOCK_PRODUCTS) + 1,
            'name': request.data.get('name', 'Новый товар'),
            'price': request.data.get('price', 0),
            'owner_id': request.current_user.id,
        }
        MOCK_PRODUCTS.append(new_product)
        return Response(new_product, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    """
    GET    /api/business/products/<id>/  — детали товара
    PATCH  /api/business/products/<id>/  — редактировать
    DELETE /api/business/products/<id>/  — удалить
    """

    def _get_product(self, pk):
        return next((p for p in MOCK_PRODUCTS if p['id'] == pk), None)

    @login_required
    def get(self, request, pk):
        from apps.access.permissions import has_permission
        product = self._get_product(pk)
        if not product:
            return Response({'detail': 'Не найдено.'}, status=404)

        # read_all — видит любой; read — только свои
        if has_permission(request.current_user, 'products', 'read_all'):
            return Response(product)
        if has_permission(request.current_user, 'products', 'read') and \
                product['owner_id'] == request.current_user.id:
            return Response(product)
        return Response({'detail': 'Доступ запрещён.'}, status=403)

    @login_required
    def patch(self, request, pk):
        from apps.access.permissions import has_permission
        product = self._get_product(pk)
        if not product:
            return Response({'detail': 'Не найдено.'}, status=404)

        if has_permission(request.current_user, 'products', 'update_all'):
            product.update(request.data)
            return Response(product)
        if has_permission(request.current_user, 'products', 'update') and \
                product['owner_id'] == request.current_user.id:
            product.update(request.data)
            return Response(product)
        return Response({'detail': 'Доступ запрещён.'}, status=403)

    @login_required
    def delete(self, request, pk):
        from apps.access.permissions import has_permission
        product = self._get_product(pk)
        if not product:
            return Response({'detail': 'Не найдено.'}, status=404)

        if has_permission(request.current_user, 'products', 'delete_all'):
            MOCK_PRODUCTS.remove(product)
            return Response(status=204)
        if has_permission(request.current_user, 'products', 'delete') and \
                product['owner_id'] == request.current_user.id:
            MOCK_PRODUCTS.remove(product)
            return Response(status=204)
        return Response({'detail': 'Доступ запрещён.'}, status=403)


# ─── Заказы ──────────────────────────────────────────────────────────────────

class OrderListView(APIView):
    """GET /api/business/orders/ — список заказов."""

    @login_required
    def get(self, request):
        from apps.access.permissions import has_permission
        if has_permission(request.current_user, 'orders', 'read_all'):
            return Response({'orders': MOCK_ORDERS})
        if has_permission(request.current_user, 'orders', 'read'):
            my_orders = [o for o in MOCK_ORDERS if o['owner_id'] == request.current_user.id]
            return Response({'orders': my_orders})
        return Response({'detail': 'Доступ запрещён.'}, status=403)

    @permission_required('orders', 'create')
    def post(self, request):
        new_order = {
            'id': len(MOCK_ORDERS) + 1,
            'product_id': request.data.get('product_id', 1),
            'status': 'pending',
            'owner_id': request.current_user.id,
        }
        MOCK_ORDERS.append(new_order)
        return Response(new_order, status=201)


# ─── Магазины ────────────────────────────────────────────────────────────────

class ShopListView(APIView):
    """GET /api/business/shops/ — список магазинов."""

    @permission_required('shops', 'read_all')
    def get(self, request):
        return Response({'shops': MOCK_SHOPS})

    @permission_required('shops', 'create')
    def post(self, request):
        new_shop = {
            'id': len(MOCK_SHOPS) + 1,
            'name': request.data.get('name', 'Новый магазин'),
            'city': request.data.get('city', ''),
            'owner_id': request.current_user.id,
        }
        MOCK_SHOPS.append(new_shop)
        return Response(new_shop, status=201)
