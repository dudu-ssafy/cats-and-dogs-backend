from ..models.shop import Product
from django.shortcuts import get_object_or_404
from django.db.models import QuerySet

class ProductService:

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
