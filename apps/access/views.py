from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Role, BusinessElement, AccessRule, UserRole
from .serializers import (
    RoleSerializer, BusinessElementSerializer,
    AccessRuleSerializer, AccessRuleUpdateSerializer, UserRoleSerializer
)
from .permissions import admin_required


# ─── Роли ────────────────────────────────────────────────────────────────────

class RoleListView(APIView):
    """GET /api/access/roles/ — список ролей  |  POST — создать роль."""

    @admin_required
    def get(self, request):
        roles = Role.objects.all()
        return Response(RoleSerializer(roles, many=True).data)

    @admin_required
    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        role = serializer.save()
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    """GET/PATCH/DELETE /api/access/roles/<id>/"""

    def get_object(self, pk):
        try:
            return Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return None

    @admin_required
    def get(self, request, pk):
        role = self.get_object(pk)
        if not role:
            return Response({'detail': 'Не найдено.'}, status=404)
        return Response(RoleSerializer(role).data)

    @admin_required
    def patch(self, request, pk):
        role = self.get_object(pk)
        if not role:
            return Response({'detail': 'Не найдено.'}, status=404)
        serializer = RoleSerializer(role, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(serializer.data)

    @admin_required
    def delete(self, request, pk):
        role = self.get_object(pk)
        if not role:
            return Response({'detail': 'Не найдено.'}, status=404)
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Бизнес-объекты ──────────────────────────────────────────────────────────

class BusinessElementListView(APIView):
    """GET /api/access/elements/  |  POST — создать элемент."""

    @admin_required
    def get(self, request):
        elements = BusinessElement.objects.all()
        return Response(BusinessElementSerializer(elements, many=True).data)

    @admin_required
    def post(self, request):
        serializer = BusinessElementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        return Response(BusinessElementSerializer(serializer.save()).data, status=201)


# ─── Правила доступа ─────────────────────────────────────────────────────────

class AccessRuleListView(APIView):
    """GET /api/access/rules/  |  POST — создать правило."""

    @admin_required
    def get(self, request):
        rules = AccessRule.objects.select_related('role', 'element').all()
        return Response(AccessRuleSerializer(rules, many=True).data)

    @admin_required
    def post(self, request):
        serializer = AccessRuleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        rule = serializer.save()
        return Response(AccessRuleSerializer(rule).data, status=201)


class AccessRuleDetailView(APIView):
    """GET/PATCH/DELETE /api/access/rules/<id>/"""

    def get_object(self, pk):
        try:
            return AccessRule.objects.select_related('role', 'element').get(pk=pk)
        except AccessRule.DoesNotExist:
            return None

    @admin_required
    def get(self, request, pk):
        rule = self.get_object(pk)
        if not rule:
            return Response({'detail': 'Не найдено.'}, status=404)
        return Response(AccessRuleSerializer(rule).data)

    @admin_required
    def patch(self, request, pk):
        rule = self.get_object(pk)
        if not rule:
            return Response({'detail': 'Не найдено.'}, status=404)
        serializer = AccessRuleUpdateSerializer(rule, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(AccessRuleSerializer(rule).data)

    @admin_required
    def delete(self, request, pk):
        rule = self.get_object(pk)
        if not rule:
            return Response({'detail': 'Не найдено.'}, status=404)
        rule.delete()
        return Response(status=204)


# ─── Назначение ролей пользователям ─────────────────────────────────────────

class UserRoleListView(APIView):
    """GET /api/access/user-roles/  |  POST — назначить роль пользователю."""

    @admin_required
    def get(self, request):
        user_roles = UserRole.objects.select_related('user', 'role').all()
        return Response(UserRoleSerializer(user_roles, many=True).data)

    @admin_required
    def post(self, request):
        serializer = UserRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        user_role = serializer.save()
        return Response(UserRoleSerializer(user_role).data, status=201)


class UserRoleDetailView(APIView):
    """DELETE /api/access/user-roles/<id>/ — отозвать роль."""

    @admin_required
    def delete(self, request, pk):
        try:
            ur = UserRole.objects.get(pk=pk)
        except UserRole.DoesNotExist:
            return Response({'detail': 'Не найдено.'}, status=404)
        ur.delete()
        return Response(status=204)
