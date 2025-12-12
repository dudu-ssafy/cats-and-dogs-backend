from rest_framework import viewsets
from rest_framework.response import Response
from ..serializers.shop import ProductListSerializer,ProductDetailSerializer
from ..models.shop import Product
from ..services.shop import ProductService

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    
    def retrieve(self, request, pk=None):
        """
        특정 상품의 상세 정보를 조회하고 JSON 응답을 반환합니다. 
        (GET /products/{pk}/)
        """
        product_instance = ProductService.get_product_detail(pk=pk)
        serializer = ProductDetailSerializer(product_instance) 
        
        return Response(serializer.data)
