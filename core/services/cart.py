# core/services/cart.py
from ..models.cart import Basket,BasketItem
from rest_framework.exceptions import APIException
from rest_framework import status
from django.db import transaction


class InvalidQuantityError(APIException):
    """수량이 유효하지 않을 때 발생하는 예외"""
    status_code = status.HTTP_400_BAD_REQUEST 
    default_detail = '상품 수량은 1 이상이어야 합니다.'
    default_code = 'invalid_quantity'

class CartService:
    BasketItem = object # 임시 객체

    @staticmethod
    @transaction.atomic
    def add_or_update_basket_item(user, option_id: int, quantity: int):
        """
        장바구니 항목 추가/업데이트 로직. try-except 없음.
        """
        
        if quantity <= 0:
            raise InvalidQuantityError() # Service 내부 예외를 바로 발생시킵니다.

        return {"option_id": option_id, "new_quantity": quantity}
    
    @staticmethod
    def get_user_cart_items(user):
        """
        장바구니 항목 목록을 조회합니다.
        (이전 단계에서 이 메서드는 Basket 객체에서 항목을 가져오도록 구현했습니다.)
        """
        basket = CartService.get_user_basket(user)
        
        return basket.items.all().select_related('option__product')
    

    @staticmethod
    def get_user_basket(user):
        """
        주어진 사용자의 Basket 객체를 가져오거나 생성합니다.
        (View에서 호출될 때 Http404 대신 항상 Basket 객체를 반환합니다.)
        """
        basket, created = Basket.objects.get_or_create(user=user)
        return basket