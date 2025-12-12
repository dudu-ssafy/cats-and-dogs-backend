# core/views/cart.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..services.cart import CartService 
from ..serializers.cart import BasketSerializer

class CartManageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        option_id = request.data.get('option_id')
        # quantity가 없을 경우 기본값 1 사용
        quantity = int(request.data.get('quantity', 1)) 
        
        result = CartService.add_or_update_basket_item(
            user=request.user, 
            option_id=option_id, 
            quantity=quantity
        )
            
        return Response(
            {"message": "장바구니가 업데이트되었습니다.", "data": result}, 
            status=status.HTTP_201_CREATED
        )


    def get(self, request):
        """사용자의 장바구니 내용을 조회합니다."""
        
        basket = CartService.get_user_basket(request.user) 
        if not basket:
            
            return Response({"items": []}, status=status.HTTP_200_OK)
            
        serializer = BasketSerializer(basket)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
