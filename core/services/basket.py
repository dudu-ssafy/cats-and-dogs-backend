# core/services/cart.py
from core.models.basket import Basket,BasketItem
from rest_framework.exceptions import APIException
from rest_framework import status
from django.db import transaction
from core.models.shop import ProductOption

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
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        
        option = None
        product = None

        if option_id:
            option = ProductOption.objects.get(id=option_id)
            product = option.product
        elif product_id:
            # 옵션 없이 상품 ID로 직접 추가하는 경우
            from core.models.shop import Product
            product = Product.objects.get(id=product_id)
        
        # 상품/옵션 식별 불가 시 에러 (Serializer에서 걸렀겠지만 안전장치)
        if not product:
             raise APIException("상품을 찾을 수 없습니다.")

        try:
            # 기존 항목 검색 조건: basket, product, option(nullable)
            item = BasketItem.objects.get(
                basket=basket,
                option=option, # None일 수 있음
                product=product
            )
            item.quantity += quantity
            item.save()
        except BasketItem.DoesNotExist:
            item = BasketItem.objects.create(
                basket=basket,
                option=option, # None일 수 있음
                product=product,
                quantity=quantity
            )

        return {"product_id": product.id, "option_id": option.id if option else None, "new_quantity": quantity}

    def remove_item_from_basket(self, user, item_id):
        """장바구니 항목 삭제"""
        basket = self.get_user_basket(user)
        try:
            item = BasketItem.objects.get(id=item_id, basket=basket)
            item.delete()
            return True
        except BasketItem.DoesNotExist:
            return False

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
