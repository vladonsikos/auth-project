from rest_framework import serializers
from .models import Role, BusinessElement, AccessRule, UserRole


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']


class BusinessElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessElement
        fields = ['id', 'name', 'description']


class AccessRuleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    element_name = serializers.CharField(source='element.name', read_only=True)

    class Meta:
        model = AccessRule
        fields = [
            'id', 'role', 'role_name', 'element', 'element_name',
            'read', 'read_all', 'create', 'update', 'update_all',
            'delete', 'delete_all',
        ]


class AccessRuleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRule
        fields = [
            'read', 'read_all', 'create', 'update', 'update_all',
            'delete', 'delete_all',
        ]


class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserRole
        fields = ['id', 'user', 'user_email', 'role', 'role_name', 'assigned_at']
        read_only_fields = ['assigned_at']
