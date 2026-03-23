"""
Views для аутентификации: регистрация, вход, выход, профиль, CRUD пользователей.
Все операции делегируются в AuthService — views только HTTP-слой.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import models

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, UpdateUserSerializer, CreateUserSerializer
from .services import AuthService
from .models import User
from apps.access.permissions import login_required, admin_required


class RegisterView(APIView):
    """POST /api/auth/register/ — регистрация нового пользователя."""

    def post(self, request):
        """
        Создаёт пользователя и назначает роль 'user' по умолчанию.

        Body: first_name, last_name, patronymic?, email, password, password_confirm
        Returns: 201 с данными пользователя или 400 при ошибке валидации
        """
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = AuthService.register(serializer.validated_data)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login/ — вход в систему, получение JWT-токена."""

    def post(self, request):
        """
        Проверяет учётные данные и возвращает JWT-токен.

        Body: email, password
        Returns: 200 с токеном и данными пользователя, 401 при неверных данных
        """
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        result = AuthService.login(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        if not result:
            return Response(
                {'detail': 'Неверный email или пароль.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response({
            'token': result['token'],
            'expires_at': result['expires_at'].isoformat(),
            'user': UserSerializer(result['user']).data,
        })


class LogoutView(APIView):
    """POST /api/auth/logout/ — выход из системы."""

    @login_required
    def post(self, request):
        """
        Деактивирует текущую сессию по токену из заголовка.

        Headers: Authorization: Bearer <token>
        Returns: 200
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token = auth_header[7:] if auth_header.startswith('Bearer ') else ''
        AuthService.logout(token)
        return Response({'detail': 'Вы успешно вышли из системы.'})


class ProfileView(APIView):
    """GET/PATCH /api/auth/profile/ — просмотр и редактирование профиля."""

    @login_required
    def get(self, request):
        """
        Возвращает данные текущего пользователя.

        Returns: 200 с данными пользователя
        """
        return Response(UserSerializer(request.current_user).data)

    @login_required
    def patch(self, request):
        """
        Обновляет поля профиля (частичное обновление).

        Body: first_name?, last_name?, patronymic?, email?
        Returns: 200 с обновлёнными данными или 400 при ошибке валидации
        """
        serializer = UpdateUserSerializer(
            data=request.data,
            context={'user': request.current_user},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = AuthService.update_profile(request.current_user, serializer.validated_data)
        return Response(UserSerializer(user).data)

    @login_required
    def post(self, request):
        """
        Смена пароля.

        Body: current_password, new_password, confirm_password
        Returns: 200 или 400 при ошибке
        """
        from apps.users.services import AuthService
        
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not current_password or not new_password or not confirm_password:
            return Response(
                {'detail': 'Все поля обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {'confirm_password': 'passwords_do_not_match'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем текущий пароль
        if not AuthService.check_password(request.current_user, current_password):
            return Response(
                {'current_password': 'wrong_current_password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Меняем пароль
        AuthService.change_password(request.current_user, new_password)
        return Response({'detail': 'Пароль успешно изменён'})


class DeleteAccountView(APIView):
    """DELETE /api/auth/profile/delete/ — мягкое удаление аккаунта."""

    @login_required
    def delete(self, request):
        """
        Деактивирует аккаунт и все сессии пользователя (soft delete).

        Returns: 200
        """
        AuthService.delete_account(request.current_user)
        return Response({'detail': 'Аккаунт деактивирован.'})


class UsersListView(APIView):
    """GET /api/auth/users/ — список пользователей, POST — создание."""

    @admin_required
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        search = request.query_params.get('search', '')
        role = request.query_params.get('role', '')
        is_active = request.query_params.get('is_active', None)

        users = User.objects.all()

        # Фильтрация по статусу
        if is_active is not None and is_active != '':
            users = users.filter(is_active=(is_active.lower() == 'true'))
        # Если is_active не указан или пустой — показываем всех

        # Фильтрация по роли
        if role:
            users = users.filter(user_roles__role_id=int(role))

        if search:
            users = users.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search)
            )

        start = (page - 1) * page_size
        end = start + page_size
        paginated = users[start:end]

        return Response({
            'count': users.count(),
            'next': f'/api/auth/users/?page={page + 1}&page_size={page_size}' if end < users.count() else None,
            'previous': f'/api/auth/users/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': UserSerializer(paginated, many=True).data,
        })

    @admin_required
    def post(self, request):
        """
        Создаёт нового пользователя.

        Body: first_name, last_name, patronymic?, email, password, password_confirm
        Returns: 201 с данными пользователя или 400 при ошибке
        """
        serializer = CreateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = AuthService.register(serializer.validated_data)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    """GET/PATCH/DELETE /api/auth/users/{id}/ — детали, обновление, удаление."""

    @admin_required
    def get(self, request, user_id):
        """Возвращает данные пользователя по ID."""
        try:
            user = User.objects.get(id=user_id)
            return Response(UserSerializer(user).data)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

    @admin_required
    def patch(self, request, user_id):
        """Обновляет пользователя по ID."""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateUserSerializer(data=request.data, context={'user': user}, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Обновляем поля пользователя
        user = AuthService.update_profile(user, serializer.validated_data)
        
        # Если указана роль, обновляем её
        role_id = serializer.validated_data.get('role')
        if role_id:
            from apps.access.models import Role, UserRole
            # Удаляем старые роли
            UserRole.objects.filter(user=user).delete()
            # Добавляем новую роль
            role = Role.objects.filter(id=role_id).first()
            if role:
                UserRole.objects.create(user=user, role=role)
        
        return Response(UserSerializer(user).data)

    @admin_required
    def delete(self, request, user_id):
        """Удаляет пользователя по ID."""
        try:
            user = User.objects.get(id=user_id)
            user.delete()
            return Response({'detail': 'Пользователь удалён'})
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)


class BulkDeleteUsersView(APIView):
    """POST /api/auth/users/bulk_delete/ — массовое удаление пользователей."""

    @admin_required
    def post(self, request):
        """
        Удаляет пользователей по списку ID.

        Body: { ids: [1, 2, 3] }
        Returns: 200 с количеством удалённых
        """
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'detail': 'ids обязателен и должен быть списком'}, status=status.HTTP_400_BAD_REQUEST)
        deleted_count, _ = User.objects.filter(id__in=ids).delete()
        return Response({'deleted': deleted_count})
