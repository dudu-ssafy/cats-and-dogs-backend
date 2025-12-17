from django.db import models
from .order import Order

class Payment(models.Model):
    order = models.OneToOneField(
        Order, 
        on_delete=models.CASCADE, 
        related_name='payment',
        verbose_name='주문'
    )
    imp_uid = models.CharField(
        '포트원 결제 고유 UID',
        max_length=100, 
        null=True, 
        blank=True
    )
    amount = models.PositiveIntegerField(
        '결제 금액'
    )
    status = models.CharField(
        'PG사 결제 상태',
        max_length=50,
        help_text='ready, paid, cancelled, failed 등'
    )
    response_json = models.JSONField(
        'PG사 응답 전문',
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(
        '생성 일시',
        auto_now_add=True
    )

    class Meta:
        db_table = 'payment'
        verbose_name = '결제 로그'
        verbose_name_plural = '결제 로그 목록'

    def __str__(self):
        return f'{self.order.merchant_uid} - {self.status}'
