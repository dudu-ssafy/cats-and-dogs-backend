from rest_framework import serializers
from django.db.models import Sum, F
from core.models.basket import Basket, BasketItem
from core.models import ProductOption 
from django.db import models

class BasketItemSerializer(serializers.ModelSerializer):
    """
    장바구니 항목 생성 및 상세 조회용 시리얼라이저
    """
    product_name = serializers.CharField(source='option.product.title', read_only=True)
    option_value = serializers.CharField(source='option.value', read_only=True)
    option_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = BasketItem
        fields = ['id', 'option_id', 'quantity', 
                  'product_name', 'option_value', 'price_at_addition']
        read_only_fields = ['id', 'price_at_addition', 'product_name', 'option_value']

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
        aggregation_result = obj.items.aggregate(
            total=Sum(F('price_at_addition') * F('quantity'), output_field=models.DecimalField())
        )['total']
        
        return aggregation_result if aggregation_result is not None else 0


class BasketItemAddSerializer(serializers.ModelSerializer):
    """
    장바구니 항목 추가용 시리얼라이저
    """
    product_option_id = serializers.IntegerField(write_only=True, required=True)
    quantity = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = BasketItem
        fields = ['product_option_id', 'quantity']
