from datetime import datetime, timezone
from .utils import decode_token


class JWTAuthMiddleware:
    """
    Кастомный Middleware для аутентификации через JWT.
    Извлекает токен из заголовка Authorization: Bearer <token>,
    валидирует его и устанавливает request.user_id и request.current_user.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user_id = None
        request.current_user = None

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            payload = decode_token(token)
            if payload:
                # Проверяем сессию в БД
                try:
                    from .models import Session, User
                    session = Session.objects.filter(
                        token=token,
                        is_active=True,
                        expires_at__gt=datetime.now(timezone.utc)
                    ).select_related('user').first()

                    if session and session.user.is_active:
                        request.user_id = session.user.id
                        request.current_user = session.user
                except Exception:
                    pass

        response = self.get_response(request)
        return response
