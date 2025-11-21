from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from core.views import board, user

app_name = 'core'

v1_router = DefaultRouter()
v1_router.register('boards', board.BoardViewSet, basename='board')
v1_router.register('users', user.UserViewSet, basename='user')


urlpatterns = [
    path('', include(v1_router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
