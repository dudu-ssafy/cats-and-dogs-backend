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

    @staticmethod
    def toss_payment():
        import base64
        secrey_key = settings.TOSS_PAYMENT_KEY
        ENCRYPTED_SECRET_KEY = base64.b64encode(f"{secrey_key}:".encode("utf-8")).decode("utf-8")
        AUTHORIZATION_HEADER = f"Basic {ENCRYPTED_SECRET_KEY}"
        
        amount = 100
        order_id = 123
        payment_key = 'test_key'
        url = "https://api.tosspayments.com/v1/payments/confirm"

        headers = {
            "Authorization": AUTHORIZATION_HEADER,
            "Content-Type": "application/json",
        }

        payload = {
            "paymentKey": payment_key,
            "amount": amount,
            "orderId": order_id,
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            print(response)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"[Toss Payment Error] {e}")
            return None

    @staticmethod
    def kakao_payment_ready(order):
        order_items = order.items.all()
        item_name = order_items.first().product.title
        if order_items.count() > 1:
            item_name += f" 외 {order_items.count() - 1}건"

        url = "https://open-api.kakaopay.com/online/v1/payment/ready"
        headers = {
            "Authorization": 'SECRET_KEY '+ settings.KAKAO_SECRET_KEY, 
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        body = {
            "cid": "TC0ONETIME", # Test CID
            "partner_order_id": order.merchant_uid,
            "partner_user_id": str(order.user.id),
            "item_name": item_name,
            "quantity": order_items.count(),         # Total logic could be complex, simplifying for total amount
            "total_amount": int(order.total_amount),
            "vat_amount": 0,    
            "tax_free_amount": 0,
            "approval_url": f"http://127.0.0.1:8000/api/v1/payments/kakao_redirect?merchant_uid={order.merchant_uid}",
            "fail_url": f"http://127.0.0.1:8000/api/v1/payments/kakao_redirect?merchant_uid={order.merchant_uid}",
            "cancel_url": f"http://127.0.0.1:8000/api/v1/payments/kakao_redirect?merchant_uid={order.merchant_uid}",
            "payment_method_type": "MONEY"
        }

        try:
            response = requests.post(url, headers=headers, json=body)
            if response.status_code == 400:
                print(f"카카오페이 서버 응답: {response.text}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"[Kakao Payment Error] {e}")
            return None


    @staticmethod
    def kakao_payment_approve(pg_token, tid, partner_order_id, partner_user_id):
        url = 'https://open-api.kakaopay.com/online/v1/payment/approve'
        headers = {
            "Authorization": 'SECRET_KEY '+ settings.KAKAO_SECRET_KEY, 
            "Content-Type": "application/json",
        }

        data = {
            "cid": "TC0ONETIME",
            "partner_order_id": partner_order_id,
            "partner_user_id": partner_user_id,
            "tid": tid,
            "pg_token": pg_token,
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()
            
            if response.status_code != 200:
                 logger.error(f"[Kakao Approve Fail] {response.text}")
                 return None

            return response_json
        except requests.exceptions.RequestException as e:
            logger.error(f"[Kakao Payment Error] {e}")
            return None

