from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from core.serializers.user import UserCreateSerializer, LoginSerializer, LogoutSerializer, UserDetailSerializer
from core.services.user import UserService
from django.shortcuts import redirect
import requests
from core.services.user import AuthService

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
            return Response({
                'token': token,
                'user': UserDetailSerializer(user).data,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def oauth_login(self, request):
        to = request.GET.get('to')
        if to == 'naver':
            return redirect(
                AuthService.get_naver_login_url()
            )
        elif to == 'google':
            return redirect(
                AuthService.get_google_login_url()
            )

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def oauth_login_callback(self, request):
        provider = request.GET.get('to')
        if provider == 'naver':
            tokens = AuthService.handle_naver_callback(
                code=request.GET.get('code'),
                state=request.GET.get('state')
            )
        elif provider == 'google':
            tokens = AuthService.handle_google_callback(
                code=request.GET.get('code'),
                state=request.GET.get('state')
            )
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 프론트엔드 로그인 페이지로 토큰과 함께 리다이렉트
        frontend_login_url = f"{settings.FRONTEND_URL}/login"
        redirect_url = f"{frontend_login_url}?access={tokens['access']}&refresh={tokens['refresh']}"
        return redirect(redirect_url)


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

    @action(detail=False, methods=['patch'])
    def info_edit(self, request):
        updated_user = UserService.info_edit(
            user=request.user,
            username=request.data.get('username'),
            password=request.data.get('password'),
        )
        
        serializer = UserDetailSerializer(updated_user)
        return Response(serializer.data, status=status.HTTP_200_OK)