"""
Views для аутентификации: регистрация, вход, выход, профиль.
Все операции делегируются в AuthService — views только HTTP-слой.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, UpdateUserSerializer
from .services import AuthService
from apps.access.permissions import login_required


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

        Returns: 200 с данными профиля
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
