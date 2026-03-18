from django.urls import path
from .views import RegisterView, LoginView, LogoutView, ProfileView, DeleteAccountView, UsersListView, UserDetailView, BulkDeleteUsersView
from .views_logs import LogView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/delete/', DeleteAccountView.as_view(), name='delete-account'),
    path('logs/', LogView.as_view(), name='logs'),
    path('users/', UsersListView.as_view(), name='users-list'),
    path('users/bulk_delete/', BulkDeleteUsersView.as_view(), name='users-bulk-delete'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
]
