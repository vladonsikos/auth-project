from django.urls import path, include

urlpatterns = [
    path('api/auth/', include('apps.users.urls')),
    path('api/access/', include('apps.access.urls')),
    path('api/business/', include('apps.business.urls')),
]
