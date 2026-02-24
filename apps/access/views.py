"""
Views для управления ролями, правилами доступа и назначением ролей.
Доступны только администраторам. Логика делегируется в сервисы.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404

from .models import Role, BusinessElement, AccessRule, UserRole
from .serializers import (
    RoleSerializer, BusinessElementSerializer,
    AccessRuleSerializer, AccessRuleUpdateSerializer, UserRoleSerializer,
)
from .services import RoleService, AccessRuleService, UserRoleService
from .permissions import admin_required


class RoleListView(APIView):
    """GET /api/access/roles/ — список ролей | POST — создать роль."""

    @admin_required
    def get(self, request):
        """Возвращает список всех ролей."""
        roles = RoleService.list_roles()
        return Response(RoleSerializer(roles, many=True).data)

    @admin_required
    def post(self, request):
        """
        Создаёт новую роль.

        Body: name, description?
        Returns: 201 или 400
        """
        serializer = RoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        role = serializer.save()
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    """GET/PATCH/DELETE /api/access/roles/<pk>/"""

    @admin_required
    def get(self, request, pk):
        """Возвращает роль по ID. 404 если не найдена."""
        role = get_object_or_404(Role, pk=pk)
        return Response(RoleSerializer(role).data)

    @admin_required
    def patch(self, request, pk):
        """
        Частично обновляет роль.

        Body: name?, description?
        Returns: 200 или 400
        """
        role = get_object_or_404(Role, pk=pk)
        serializer = RoleSerializer(role, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    @admin_required
    def delete(self, request, pk):
        """Удаляет роль. 404 если не найдена."""
        role = get_object_or_404(Role, pk=pk)
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BusinessElementListView(APIView):
    """GET /api/access/elements/ | POST — создать бизнес-объект."""

    @admin_required
    def get(self, request):
        """Возвращает список всех бизнес-объектов."""
        elements = BusinessElement.objects.all()
        return Response(BusinessElementSerializer(elements, many=True).data)

    @admin_required
    def post(self, request):
        """
        Создаёт новый бизнес-объект.

        Body: name, description?
        Returns: 201 или 400
        """
        serializer = BusinessElementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            BusinessElementSerializer(serializer.save()).data,
            status=status.HTTP_201_CREATED,
        )


class AccessRuleListView(APIView):
    """GET /api/access/rules/ | POST — создать правило доступа."""

    @admin_required
    def get(self, request):
        """Возвращает все правила доступа с именами роли и объекта."""
        rules = AccessRuleService.list_rules()
        return Response(AccessRuleSerializer(rules, many=True).data)

    @admin_required
    def post(self, request):
        """
        Создаёт правило доступа роль→объект.

        Body: role, element, read?, read_all?, create?, update?, update_all?, delete?, delete_all?
        Returns: 201 или 400
        """
        serializer = AccessRuleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        rule = serializer.save()
        return Response(AccessRuleSerializer(rule).data, status=status.HTTP_201_CREATED)


class AccessRuleDetailView(APIView):
    """GET/PATCH/DELETE /api/access/rules/<pk>/"""

    @admin_required
    def get(self, request, pk):
        """Возвращает правило доступа по ID."""
        rule = get_object_or_404(AccessRule.objects.select_related('role', 'element'), pk=pk)
        return Response(AccessRuleSerializer(rule).data)

    @admin_required
    def patch(self, request, pk):
        """
        Обновляет права в правиле доступа.

        Body: любые булевые поля прав
        Returns: 200 или 400
        """
        rule = get_object_or_404(AccessRule.objects.select_related('role', 'element'), pk=pk)
        serializer = AccessRuleUpdateSerializer(rule, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        rule = AccessRuleService.update_rule(rule, serializer.validated_data)
        return Response(AccessRuleSerializer(rule).data)

    @admin_required
    def delete(self, request, pk):
        """Удаляет правило доступа."""
        rule = get_object_or_404(AccessRule, pk=pk)
        AccessRule.objects.filter(pk=rule.pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserRoleListView(APIView):
    """GET /api/access/user-roles/ | POST — назначить роль пользователю."""

    @admin_required
    def get(self, request):
        """Возвращает все назначения ролей."""
        user_roles = UserRoleService.list_user_roles()
        return Response(UserRoleSerializer(user_roles, many=True).data)

    @admin_required
    def post(self, request):
        """
        Назначает роль пользователю.

        Body: user (ID), role (ID)
        Returns: 201 или 400
        """
        serializer = UserRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user_role = serializer.save()
        return Response(UserRoleSerializer(user_role).data, status=status.HTTP_201_CREATED)


class UserRoleDetailView(APIView):
    """DELETE /api/access/user-roles/<pk>/ — отозвать роль у пользователя."""

    @admin_required
    def delete(self, request, pk):
        """Удаляет назначение роли. 404 если не найдено."""
        user_role = get_object_or_404(UserRole, pk=pk)
        UserRoleService.revoke_role(user_role)
        return Response(status=status.HTTP_204_NO_CONTENT)
