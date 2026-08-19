from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import (
    RegistrationView,
    SwaggerTokenObtainPairView,
    SwaggerTokenRefreshView,
    ForgotPasswordView,
    ResetPasswordView,
    AdminUserViewSet
)

router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-user')

urlpatterns = [
    # Auth endpoints
    path('auth/register/', RegistrationView.as_view(), name='register'),
    path('auth/login/', SwaggerTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', SwaggerTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    
    # Admin User CRUD routes
    path('', include(router.urls)),
]
