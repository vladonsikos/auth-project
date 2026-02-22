from datetime import datetime, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User, Session
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, UpdateUserSerializer
from .utils import hash_password, check_password, generate_token
from apps.access.permissions import login_required


class RegisterView(APIView):
    """POST /api/auth/register/ — Регистрация нового пользователя."""

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = User.objects.create(
            first_name=data['first_name'],
            last_name=data['last_name'],
            patronymic=data.get('patronymic', ''),
            email=data['email'],
            password_hash=hash_password(data['password']),
        )

        # Назначаем роль по умолчанию (user)
        from apps.access.models import Role, UserRole
        default_role = Role.objects.filter(name='user').first()
        if default_role:
            UserRole.objects.create(user=user, role=default_role)

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login/ — Вход в систему, получение JWT-токена."""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = User.objects.filter(email=data['email'], is_active=True).first()

        if not user or not check_password(data['password'], user.password_hash):
            return Response(
                {'detail': 'Неверный email или пароль.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, expires_at = generate_token(user.id)
        Session.objects.create(user=user, token=token, expires_at=expires_at)

        return Response({
            'token': token,
            'expires_at': expires_at.isoformat(),
            'user': UserSerializer(user).data,
        })


class LogoutView(APIView):
    """POST /api/auth/logout/ — Выход из системы (деактивация сессии)."""

    @login_required
    def post(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token = auth_header[7:] if auth_header.startswith('Bearer ') else ''
        Session.objects.filter(token=token).update(is_active=False)
        return Response({'detail': 'Вы успешно вышли из системы.'})


class ProfileView(APIView):
    """GET/PATCH /api/auth/profile/ — Просмотр и редактирование профиля."""

    @login_required
    def get(self, request):
        return Response(UserSerializer(request.current_user).data)

    @login_required
    def patch(self, request):
        serializer = UpdateUserSerializer(data=request.data, context={'user': request.current_user})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.current_user
        for field, value in serializer.validated_data.items():
            setattr(user, field, value)
        user.save()

        return Response(UserSerializer(user).data)


class DeleteAccountView(APIView):
    """DELETE /api/auth/profile/ — Мягкое удаление аккаунта."""

    @login_required
    def delete(self, request):
        user = request.current_user
        # Деактивируем все сессии
        Session.objects.filter(user=user).update(is_active=False)
        # Мягкое удаление
        user.is_active = False
        user.save()
        return Response({'detail': 'Аккаунт деактивирован.'})
