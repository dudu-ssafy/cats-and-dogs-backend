from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.serializers.user import UserCreateSerializer, LoginSerializer, LogoutSerializer, UserDetailSerializer
from core.services.user import UserService


class UserViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @extend_schema(
        request=UserCreateSerializer,
        responses={201: UserCreateSerializer},
        summary='User signup'
    )
    @action(detail=False, methods=['post'])
    def signup(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            UserService.create_user(serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=LoginSerializer,
        responses={200: {'properties': {'token': {'type': 'string'}}}},
        summary='User login'
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = UserService.authenticate_user(**serializer.validated_data)
            token = UserService.get_token(user)
            return Response(token)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=LogoutSerializer,
        responses={204: None},
        summary='User logout'
    )
    @action(detail=False, methods=['post'])
    def logout(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            UserService.logout(serializer.validated_data['refresh'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={200: UserDetailSerializer},
        summary='Get user profile'
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
