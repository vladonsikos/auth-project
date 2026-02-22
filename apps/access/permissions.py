from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def login_required(func):
    """Декоратор: требует аутентифицированного пользователя (иначе 401)."""
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        if not request.current_user:
            return Response(
                {'detail': 'Аутентификация требуется.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return func(self, request, *args, **kwargs)
    return wrapper


def has_permission(user, element_name: str, permission: str) -> bool:
    """
    Проверяет, есть ли у пользователя конкретное право на бизнес-объект.

    :param user: объект User
    :param element_name: кодовое имя бизнес-объекта (например 'products')
    :param permission: одно из: read, read_all, create, update, update_all, delete, delete_all
    :return: True / False
    """
    from .models import AccessRule, UserRole
    role_ids = UserRole.objects.filter(user=user).values_list('role_id', flat=True)
    rules = AccessRule.objects.filter(
        role_id__in=role_ids,
        element__name=element_name
    )
    for rule in rules:
        if getattr(rule, permission, False):
            return True
    return False


def permission_required(element_name: str, permission: str):
    """
    Декоратор: проверяет право доступа.
    Возвращает 401 если не аутентифицирован, 403 если нет прав.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if not request.current_user:
                return Response(
                    {'detail': 'Аутентификация требуется.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            if not has_permission(request.current_user, element_name, permission):
                return Response(
                    {'detail': 'Доступ запрещён.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(func):
    """Декоратор: только для пользователей с ролью admin."""
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        if not request.current_user:
            return Response(
                {'detail': 'Аутентификация требуется.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        from .models import UserRole
        is_admin = UserRole.objects.filter(
            user=request.current_user,
            role__name='admin'
        ).exists()
        if not is_admin:
            return Response(
                {'detail': 'Доступ запрещён. Требуется роль администратора.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return func(self, request, *args, **kwargs)
    return wrapper
