from django.db import models


class User(models.Model):
    """Пользователь системы."""
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    patronymic = models.CharField(max_length=100, blank=True, default='', verbose_name='Отчество')
    email = models.EmailField(unique=True, verbose_name='Email')
    password_hash = models.CharField(max_length=255, verbose_name='Хэш пароля')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'

    def __str__(self):
        return f'{self.last_name} {self.first_name} <{self.email}>'


class Session(models.Model):
    """Сессия пользователя (JWT-токен + метаданные)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.TextField(verbose_name='JWT-токен')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(verbose_name='Истекает')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        db_table = 'sessions'
        verbose_name = 'Сессия'
