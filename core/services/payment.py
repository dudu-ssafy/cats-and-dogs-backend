import logging
import uuid
import requests
from django.conf import settings
from django.db import transaction
from core.models import Order, OrderItem, Payment, Basket

logger = logging.getLogger('payment')

class PaymentService:
    @staticmethod
    @transaction.atomic
    def create_order(user):
        """
        장바구니의 아이템들을 주문으로 변환합니다.
        """
        try:
            basket = Basket.objects.get(user=user)
            items = basket.items.select_related('product', 'option').all()
            
            if not items.exists():
                raise ValueError("장바구니가 비어있습니다.")

            total_amount = sum(item.product.base_price * item.quantity for item in items)
            # 옵션 가격 추가 로직이 필요하다면 여기서 계산
            
            merchant_uid = f"ORD-{uuid.uuid4().hex[:12].upper()}"
            
            order = Order.objects.create(
                user=user,
                merchant_uid=merchant_uid,
                total_amount=total_amount,
                status='PENDING'
            )

            order_items = [
                OrderItem(
                    order=order,
                    product=item.product,
                    option=item.option,
                    quantity=item.quantity,
                    price=item.product.base_price # 실제 구매 가격 기록
                ) for item in items
            ]
            OrderItem.objects.bulk_create(order_items)
            
            # 장바구니 비우기 (선택 사항: 결제 완료 후 비울지, 주문 생성 시 비울지 정책 결정 필요. 보통 주문 생성 시 비우지 않음)
            # 여기서는 주문 생성만 하고 결제 완료 시 장바구니를 비우는 로직이 더 안전함.
            
            logger.info(f"[Order Created] User: {user.email}, Order: {merchant_uid}, Amount: {total_amount}")
            return order

        except Basket.DoesNotExist:
            raise ValueError("장바구니를 찾을 수 없습니다.")

    @staticmethod
    def verify_payment(merchant_uid, imp_uid, amount):
        """
        포트원 결제 검증 및 DB/File 로깅
        """
        logger.info(f"[Payment Verification Start] Merchant: {merchant_uid}, ImpUID: {imp_uid}, Amount: {amount}")
        
        try:
            order = Order.objects.get(merchant_uid=merchant_uid)
        except Order.DoesNotExist:
            logger.error(f"[Payment Failed] Order not found: {merchant_uid}")
            return None

        # 1. 포트원 토큰 발급 (실제 연동 시 구현 필요)
        # 2. 결제 정보 조회 (실제 연동 시 구현 필요)
        # 여기서는 검증 성공했다고 가정하고 로직 진행
        
        # 실제로는 Portone API를 호출하여 status와 amount를 확인해야 함
        payment_status = 'paid' # Mock status
        
        # DB에 결제 로그 저장
        payment = Payment.objects.create(
            order=order,
            imp_uid=imp_uid,
            amount=amount,
            status=payment_status,
            response_json={'mock': 'data', 'status': payment_status} # 실제 응답값 저장
        )

        if payment_status == 'paid' and order.total_amount == amount:
            order.status = 'PAID'
            order.save()
            logger.info(f"[Payment Success] Order: {merchant_uid} verified.")
            
            # 결제 성공 시 장바구니 비우기
            Basket.objects.filter(user=order.user).delete()
            
            return payment
        
        else:
            order.status = 'FAILED'
            order.save()
            logger.warning(f"[Payment Mismatch] Order: {merchant_uid}, Status: {payment_status}, Amount: {amount} vs {order.total_amount}")
            return payment
