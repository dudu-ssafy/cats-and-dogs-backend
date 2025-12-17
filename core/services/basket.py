# core/services/cart.py
from core.models.basket import Basket,BasketItem
from rest_framework.exceptions import APIException
from rest_framework import status
from django.db import transaction


class InvalidQuantityError(APIException):
    """수량이 유효하지 않을 때 발생하는 예외"""
    status_code = status.HTTP_400_BAD_REQUEST 
    default_detail = '상품 수량은 1 이상이어야 합니다.'
    default_code = 'invalid_quantity'

class BasketService:
    
    @transaction.atomic
    def add_or_update_basket_item(self, user, data):
        """
        장바구니 항목 추가/업데이트 로직. try-except 없음.
        """

        basket = self.get_user_basket(user)
        option_id = data.get('product_option_id')
        quantity = data.get('quantity')

        try:
            item = BasketItem.objects.get(
                basket=basket, 
                option_id=option_id
            )
            item.quantity += quantity
            item.save()
        except BasketItem.DoesNotExist:
            item = BasketItem.objects.create(
                basket=basket,
                option_id=option_id,
                quantity=quantity
            )

        return {"option_id": option_id, "new_quantity": quantity}
    
    def get_user_cart_items(self, user):
        """
        장바구니 항목 목록을 조회합니다.
        (이전 단계에서 이 메서드는 Basket 객체에서 항목을 가져오도록 구현했습니다.)
        """
        basket = self.get_user_basket(user)

        return basket.items.all().select_related('option__product')


    def get_user_basket(self, user):
        """
        주어진 사용자의 Basket 객체를 가져오거나 생성합니다.
        (View에서 호출될 때 Http404 대신 항상 Basket 객체를 반환합니다.)
        """
        basket, created = Basket.objects.get_or_create(user=user)
        return basket
