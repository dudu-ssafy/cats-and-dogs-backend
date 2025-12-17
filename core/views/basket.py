from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.services.basket import BasketService 
from core.serializers.basket import BasketSerializer, BasketItemAddSerializer

class BasketManageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BasketItemAddSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            user = request.user
            result = BasketService().add_or_update_basket_item(
                user=user, 
                data=data
            )
            return Response({
                "message": "장바구니가 업데이트되었습니다.",
                "data": result,
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    def get(self, request):
        """사용자의 장바구니 내용을 조회합니다."""
        
        basket = BasketService().get_user_basket(request.user) 
        if not basket:
            
            return Response({"items": []}, status=status.HTTP_200_OK)
            
        serializer = BasketSerializer(basket)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
