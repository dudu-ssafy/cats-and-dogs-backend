from ..models.shop import Product
from django.shortcuts import get_object_or_404
from django.db.models import QuerySet

class ProductService:

    @staticmethod
    def get_product_detail(pk: int) -> Product:
        """
        주어진 PK로 상품 객체를 조회합니다. 객체가 없으면 Http404를 발생시킵니다.
        (View에서 try-except 블록이 필요 없게 해주는 핵심 메서드)
        """
        return get_object_or_404(Product, pk=pk)

    @staticmethod
    def check_stock_status(pk: int) -> bool:
        """
        특정 상품의 재고가 남아 있는지 확인합니다. try-except를 사용하지 않습니다.
        """
        has_stock = Product.objects.filter(pk=pk, stock__gt=0).exists()
        
        return has_stock