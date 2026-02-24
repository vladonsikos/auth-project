"""
Service Layer для управления ролями, правилами доступа и назначением ролей.
"""

from .models import Role, BusinessElement, AccessRule, UserRole


class RoleService:
    """Сервис управления ролями."""

    @staticmethod
    def list_roles():
        """Возвращает QuerySet всех ролей."""
        return Role.objects.all()

    @staticmethod
    def create_role(validated_data: dict) -> Role:
        """
        Создаёт новую роль.

        Args:
            validated_data: данные из RoleSerializer

        Returns:
            Созданный объект Role
        """
        return Role.objects.create(**validated_data)


class AccessRuleService:
    """Сервис управления правилами доступа."""

    @staticmethod
    def list_rules():
        """Возвращает QuerySet всех правил с prefetch роли и элемента."""
        return AccessRule.objects.select_related('role', 'element').all()

    @staticmethod
    def update_rule(rule: AccessRule, validated_data: dict) -> AccessRule:
        """
        Обновляет поля правила доступа.

        Args:
            rule:           объект AccessRule
            validated_data: провалидированные данные

        Returns:
            Обновлённый объект AccessRule
        """
        for field, value in validated_data.items():
            setattr(rule, field, value)
        rule.save()
        return rule


class UserRoleService:
    """Сервис назначения и отзыва ролей у пользователей."""

    @staticmethod
    def list_user_roles():
        """Возвращает QuerySet всех назначений ролей."""
        return UserRole.objects.select_related('user', 'role').all()

    @staticmethod
    def assign_role(user_id: int, role_id: int) -> UserRole:
        """
        Назначает роль пользователю.

        Args:
            user_id: ID пользователя
            role_id: ID роли

        Returns:
            Созданный объект UserRole

        Raises:
            IntegrityError если роль уже назначена
        """
        return UserRole.objects.create(user_id=user_id, role_id=role_id)

    @staticmethod
    def revoke_role(user_role: UserRole) -> None:
        """
        Отзывает роль у пользователя.

        Args:
            user_role: объект UserRole
        """
        user_role.delete()
