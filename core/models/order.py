from django.db import models
from django.conf import settings
from .shop import Product, ProductOption

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', '결제 대기'),
        ('PAID', '결제 완료'),
        ('CANCELLED', '주문 취소'),
        ('FAILED', '결제 실패'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='orders',
        verbose_name='주문자'
    )
    merchant_uid = models.CharField(
        '주문 번호',
        max_length=100, 
        unique=True
    )
    status = models.CharField(
        '주문 상태',
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING'
    )
    total_amount = models.PositiveIntegerField(
        '총 결제 금액'
    )
    created_at = models.DateTimeField(
        '주문 일시',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        '수정 일시',
        auto_now=True
    )

    class Meta:
        db_table = 'order'
        verbose_name = '주문'
        verbose_name_plural = '주문 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.merchant_uid} - {self.user.username}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='주문'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT,
        verbose_name='상품'
    )
    option = models.ForeignKey(
        ProductOption, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='옵션'
    )
    quantity = models.PositiveIntegerField(
        '수량'
    )
    price = models.PositiveIntegerField(
        '구매 단가',
        help_text='구매 시점의 개당 가격'
    )

    class Meta:
        db_table = 'order_item'
        verbose_name = '주문 상품'
        verbose_name_plural = '주문 상품 목록'

    def __str__(self):
        return f'{self.order.merchant_uid} - {self.product.title}'
