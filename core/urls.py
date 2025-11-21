from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import board

app_name = 'core'

v1_router = DefaultRouter()
v1_router.register('boards', board.BoardViewSet, basename='board')

urlpatterns = [
    path('', include(v1_router.urls))
]
