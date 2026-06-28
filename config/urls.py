from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Schema Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API Version 1
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/friends/', include('apps.friends.urls')),
    path('api/v1/', include('apps.messaging.urls')), # Conversational URLs mapped directly under v1
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/parties/', include('apps.party.urls')),
    path('api/v1/communities/', include('apps.communities.urls')),
    path('api/v1/', include('apps.games.urls')), # games/ and matches/ mapped dynamically
    path('api/v1/', include('apps.progression.urls')), # progression/, achievements/ etc
    path('api/v1/', include('apps.economy.urls')), # wallet/, shop/, inventory/
]
