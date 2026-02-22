from django.urls import path
from .views import (
    RoleListView, RoleDetailView,
    BusinessElementListView,
    AccessRuleListView, AccessRuleDetailView,
    UserRoleListView, UserRoleDetailView,
)

urlpatterns = [
    path('roles/', RoleListView.as_view(), name='role-list'),
    path('roles/<int:pk>/', RoleDetailView.as_view(), name='role-detail'),
    path('elements/', BusinessElementListView.as_view(), name='element-list'),
    path('rules/', AccessRuleListView.as_view(), name='rule-list'),
    path('rules/<int:pk>/', AccessRuleDetailView.as_view(), name='rule-detail'),
    path('user-roles/', UserRoleListView.as_view(), name='user-role-list'),
    path('user-roles/<int:pk>/', UserRoleDetailView.as_view(), name='user-role-detail'),
]
