"""
Views для логирования действий пользователей.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class LogView(APIView):
    """POST /api/logs/ — логирование действий пользователя."""

    def post(self, request):
        """
        Принимает лог-запись от фронтенда и сохраняет в консоль.

        Body: action, data, timestamp
        Returns: 200
        """
        # В production можно сохранять в БД или отправлять в Sentry
        # Сейчас просто логируем в консоль
        action = request.data.get('action', 'unknown')
        data = request.data.get('data', {})
        timestamp = request.data.get('timestamp', '')
        
        print(f'[FRONTEND LOG] {timestamp} - {action}: {data}')
        
        return Response({'detail': 'Log accepted'}, status=status.HTTP_200_OK)
