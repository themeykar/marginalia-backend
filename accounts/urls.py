from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.permissions import AllowAny

from . import views

# SimpleJWT views inherit the project-level DEFAULT_PERMISSION_CLASSES
# (IsAuthenticated), so we must explicitly override them to AllowAny.

login_view = TokenObtainPairView.as_view(permission_classes=(AllowAny,))
refresh_view = TokenRefreshView.as_view(permission_classes=(AllowAny,))

urlpatterns = [
    path('signup/', views.SignupView.as_view(), name='auth-signup'),
    path('login/', login_view, name='auth-login'),
    path('refresh/', refresh_view, name='auth-refresh'),
    path('me/', views.MeView.as_view(), name='auth-me'),
]
