from rest_framework import serializers
from django.db.models import Sum, F
from core.models.basket import Basket, BasketItem
from core.models import ProductOption 
from django.db import models

class BasketItemSerializer(serializers.ModelSerializer):
    """
    장바구니 항목 생성 및 상세 조회용 시리얼라이저
    """
    product_name = serializers.SerializerMethodField()
    option_value = serializers.SerializerMethodField()
    option_id = serializers.IntegerField(write_only=True, required=False)

    price_at_addition = serializers.SerializerMethodField()

    class Meta:
        model = BasketItem
        fields = ['id', 'option_id', 'quantity', 
                  'product_name', 'option_value', 'price_at_addition']
        read_only_fields = ['id', 'product_name', 'option_value']

    def get_price_at_addition(self, obj):
        # 현재 판매가(기본가 + 옵션가)를 반환
        base = obj.product.base_price
        add = obj.option.additional_price if obj.option else 0
        return base + add

    def get_product_name(self, obj):
        # 옵션이 있으면 옵션 통해서, 없으면 직접 제품에서 가져옴
        return obj.option.product.title if obj.option else obj.product.title

    def get_option_value(self, obj):
        return obj.option.value if obj.option else "기본"

    def validate_option_id(self, value):
        """option_id 필드에 대한 유효성 검사 (존재 여부 및 재고 확인)"""
        if not ProductOption.objects.filter(pk=value).exists():
            raise serializers.ValidationError("선택하신 상품 옵션이 존재하지 않습니다.")

        option = ProductOption.objects.get(pk=value)
        if option.stock <= 0:
            raise serializers.ValidationError("선택하신 상품 옵션은 현재 재고가 없습니다.")
        
        return option



class BasketSerializer(serializers.ModelSerializer):
    """
    사용자 장바구니 전체 조회용 시리얼라이저 (Basket List View)
    """
    items = BasketItemSerializer(many=True, read_only=True)

    total_items_count = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Basket
        fields = ['user', 'items', 'total_items_count', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_total_items_count(self, obj):
        """총 수량 계산"""

        return obj.items.aggregate(total=Sum('quantity'))['total'] or 0

    def get_total_price(self, obj):
        """총 금액 계산"""
        total_price = 0
        items = obj.items.all()
        for item in items:
            if item.option:
                price = item.option.product.base_price + item.option.additional_price
            else:
                price = item.product.base_price
            
            total_price += price * item.quantity

        return total_price


class BasketItemAddSerializer(serializers.ModelSerializer):
    """
    장바구니 항목 추가용 시리얼라이저
    """
    product_option_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    product_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    quantity = serializers.IntegerField(write_only=True, required=True)

    def validate(self, attrs):
        product_option_id = attrs.get('product_option_id')
        product_id = attrs.get('product_id')
        
        if not product_option_id and not product_id:
            raise serializers.ValidationError("product_option_id 또는 product_id 중 하나는 필수입니다.")
            
        return attrs

    class Meta:
        model = BasketItem
        fields = ['product_option_id', 'product_id', 'quantity']
