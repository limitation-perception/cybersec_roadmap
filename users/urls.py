from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("auth/register", views.RegisterView.as_view()),
    path("auth/login", TokenObtainPairView.as_view()),
    path("auth/refresh", TokenRefreshView.as_view()),
]
