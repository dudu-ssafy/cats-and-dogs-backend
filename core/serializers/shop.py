from rest_framework import serializers
from core.models.shop import Product, ProductOption, Category, ProductImage

# -----------------------------------------------------
# 1. 상세 옵션 Serializer (목록/상세 모두 사용)
class ProductOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOption
        fields = ['id', 'name', 'value', 'additional_price', 'stock']

# -----------------------------------------------------
# 2. 목록 조회용 Serializer (새로 추가)
class ProductListSerializer(serializers.ModelSerializer):
    # Category의 이름은 목록에서도 필요하므로 그대로 둡니다.
    category_name = serializers.CharField(source='category.name', read_only=True)
    main_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        # 목록 화면에 필요한 최소한의 필드만 포함합니다.
        fields = [
            'id', 'category_name', 'title', 'base_price', 
            'is_sale', 'main_image' # description, created_at, options 제외
        ]

    def get_main_image(self, obj):
        image = obj.images.filter(is_main=True).first()
        if image:
            return image.image_url
        return obj.detail_image_url # Fallback for simple admin entry

# -----------------------------------------------------
# 3. 상세 조회용 Serializer (기존 ProductSerializer 이름 변경)
class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        # 모든 상세 필드를 포함합니다.
        fields = [
            'id', 'category_name', 'title', 'description', 'base_price', 
            'is_sale', 'created_at', 'options','images', 'detail_image_url'
        ]
        read_only_fields = ['created_at']

    class ProductImageSerializer(serializers.ModelSerializer):
        class Meta:
            model = ProductImage
            fields = ['image_url', 'is_main'] # 노출 순서 등을 포함해도 됩니다.

    category_name = serializers.CharField(source='category.name', read_only=True)
    options = ProductOptionSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

