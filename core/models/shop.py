from django.db import models
from pgvector.django import VectorField

class Category(models.Model):
    """상품 카테고리 (상의, 하의, 액세서리 등)"""
    name = models.CharField(
        '카테고리명',
        max_length=100,
        unique=True,
    )
    
    class Meta:
        db_table = 'category'
        verbose_name = '상품 카테고리'
        verbose_name_plural = '상품 카테고리 목록'

    def __str__(self):
        return self.name
    

class Product(models.Model):
    """개별 상품 정보"""
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products',
        verbose_name='카테고리'
    ) 
    title = models.CharField(
        '상품명',
        max_length=200
    )
    description = models.TextField(
        '상세 설명'
    )
    embedding = VectorField(
        dimensions=1536,
        help_text='OpenAI embedding vector',
        null=True,
        blank=True
    )
    base_price = models.PositiveIntegerField(
        '기본 가격'
    )
    is_sale = models.BooleanField(
        '판매 중 여부',
        default=True # 기본값을 판매중으로 변경
    )
    detail_image_url = models.URLField(
        '상세 이미지 URL',
        max_length=2000, 
        blank=True, 
        null=True,
        help_text='상세 설명에 사용할 긴 이미지 주소'
    )
    created_at = models.DateTimeField(
        '등록일',
        auto_now_add=True
    )

    class Meta:
        db_table = 'product'
        verbose_name = '상품'
        verbose_name_plural = '상품 목록'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ProductOption(models.Model):
    """상품의 옵션 (색상, 사이즈, 재고)"""
    product = models.ForeignKey(
        Product,
        related_name='options',
        on_delete=models.CASCADE,
        verbose_name='상품'
    )
    name = models.CharField(
        '옵션 종류',
        max_length=50, 
        help_text='예: 색상, 사이즈'
    ) 
    value = models.CharField(
        '옵션 값',
        max_length=50, 
        help_text='예: 블랙, L'
    ) 
    additional_price = models.IntegerField(
        '추가 금액',
        default=0
    ) 
    stock = models.PositiveIntegerField(
        '재고 수량',
        default=0
    ) 

    class Meta:
        db_table = 'product_option'
        verbose_name = '상품 옵션'
        verbose_name_plural = '상품 옵션 목록'
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'name', 'value'],
                name='unique_product_option_combination'
            )
        ]

    def __str__(self):
        return f'{self.product.title} - {self.name}: {self.value} (재고: {self.stock})'
    

class ProductImage(models.Model):
    """상품 이미지 정보"""
    product = models.ForeignKey(
        Product,
        related_name='images', 
        on_delete=models.CASCADE,
        verbose_name='상품'
    )
    image_url = models.URLField(
        '이미지 URL',
        max_length=2000
    )
    is_main = models.BooleanField(
        '대표 이미지 여부',
        default=False
    )
    order = models.PositiveSmallIntegerField(
        '노출 순서',
        default=0
    )

    class Meta:
        db_table = 'product_image'
        verbose_name = '상품 이미지'
        verbose_name_plural = '상품 이미지 목록'
        ordering = ['order']