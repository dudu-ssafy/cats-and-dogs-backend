from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView

from core.views import board, user, shop, search
from core.views.cart import CartManageView

app_name = 'core'

v1_router = DefaultRouter()
v1_router.register('boards', board.BoardViewSet, basename='board')
v1_router.register('users', user.UserViewSet, basename='user')
v1_router.register('products', shop.ProductViewSet, basename='product')


urlpatterns = [
    path('', include(v1_router.urls)),
    path('carts/', CartManageView.as_view(), name='cart_manage'),
    path('token/pair/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('search/test/', search.VectorSearchTestView.as_view(), name='vector-search-test'),
]
