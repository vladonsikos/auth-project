from django.urls import path
from .views_logs import LogView

urlpatterns = [
    path('', LogView.as_view(), name='logs'),
]
