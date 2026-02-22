import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from django.conf import settings


def hash_password(plain_password: str) -> str:
    """Хэширует пароль с помощью bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def check_password(plain_password: str, hashed: str) -> bool:
    """Проверяет пароль против хэша."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed.encode('utf-8'))


def generate_token(user_id: int) -> tuple[str, datetime]:
    """Генерирует JWT-токен для пользователя. Возвращает (токен, expires_at)."""
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    payload = {
        'user_id': user_id,
        'exp': expires_at,
        'iat': datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
    return token, expires_at


def decode_token(token: str) -> dict | None:
    """Декодирует JWT-токен. Возвращает payload или None при ошибке."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
