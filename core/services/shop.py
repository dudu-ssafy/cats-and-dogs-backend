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
    def get_product_list(params: dict) -> QuerySet:
        queryset = Product.objects.all()

        category = params.get('category')
        if category:
            if category.isdigit():
                queryset = queryset.filter(category_id=category)
            else:
                queryset = queryset.filter(category__name__icontains=category)

        is_sale = params.get('is_sale')
        if is_sale is not None:
            is_sale_bool = is_sale.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_sale=is_sale_bool)

        min_price = params.get('min_price')
        if min_price:
            queryset = queryset.filter(base_price__gte=int(min_price))

        max_price = params.get('max_price')
        if max_price:
            queryset = queryset.filter(base_price__lte=int(max_price))

        search = params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset
