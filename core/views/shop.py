from rest_framework import viewsets
from rest_framework.response import Response
from ..serializers.shop import ProductListSerializer,ProductDetailSerializer
from ..models.shop import Product
from ..services.shop import ProductService

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    
    def get_queryset(self):
        """
        상품 목록을 조회합니다. 쿼리 파라미터로 필터링 가능합니다.
        
        사용 가능한 쿼리 파라미터:
        - category: 카테고리 ID 또는 이름
        - is_sale: 판매 중 여부 (true/false)
        - min_price: 최소 가격
        - max_price: 최대 가격
        - search: 상품명 검색

        예시: /products/?category=1&is_sale=true&min_price=10000&max_price=50000
        """
        return ProductService.get_product_list(self.request.query_params)

    def retrieve(self, request, pk=None):
        """
        특정 상품의 상세 정보를 조회하고 JSON 응답을 반환합니다. 
        (GET /products/{pk}/)
        """
        product_instance = ProductService.get_product_detail(pk=pk)
        serializer = ProductDetailSerializer(product_instance) 

        return Response(serializer.data)
