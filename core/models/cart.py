from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Basket(models.Model):
    """
    장바구니의 컨테이너 (Basket Container)
    - 사용자 1명당 장바구니 1개가 존재합니다.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='basket',
        primary_key=True, 
        verbose_name='사용자'
    )
    created_at = models.DateTimeField(
        '생성일',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        '최근 수정일',
        auto_now=True
    )

    class Meta:
        verbose_name = '장바구니'
        verbose_name_plural = '장바구니 목록'

    def __str__(self):
        return f'{self.user.username}의 장바구니'


class BasketItem(models.Model):
    """
    장바구니 항목 (Basket Item Module)
    - 장바구니에 담긴 개별 상품 정보입니다.
    """
    basket = models.ForeignKey(
        Basket,
        on_delete=models.CASCADE,
        related_name='items',  
        verbose_name='소속 장바구니'
    )
    product = models.ForeignKey(
        'core.Product',
        on_delete=models.CASCADE,
        verbose_name='상품'
    )
    
    option = models.ForeignKey(
        'core.ProductOption',
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name='선택된 옵션'
    )
    quantity = models.PositiveIntegerField(
        '수량',
        default=1
    )
    
    price_at_addition = models.DecimalField(
        '추가 시점 가격',
        max_digits=10, 
        decimal_places=2,
        null=True,
        help_text='상품 가격 변동에 대비하여 기록'
    )

    class Meta:
        db_table = 'basket_item'
        verbose_name = '장바구니 항목'
        verbose_name_plural = '장바구니 항목 목록'
        unique_together = ('basket', 'option') 