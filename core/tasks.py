import logging
from celery import shared_task
from django.db import transaction
from .models import Order, Payment, Basket
from .services.payment import PaymentService

logger = logging.getLogger('payment')

@shared_task
def process_kakao_payment_approval(pg_token, tid, merchant_uid, partner_user_id):
    logger.info(f"[Task Start] Processing payment approval for {merchant_uid}")

    # 1. Call Kakao Approve API
    approve_response = PaymentService.kakao_payment_approve(pg_token, tid, merchant_uid, partner_user_id)

    if not approve_response:
        logger.error(f"[Payment Failed] Approval API failed for {merchant_uid}")
        # Optionally update order status to FAILED
        try:
            order = Order.objects.get(merchant_uid=merchant_uid)
            order.status = 'FAILED'
            order.save()
        except Order.DoesNotExist:
            logger.error(f"[Payment Failed] Order not found during failure handling: {merchant_uid}")
            pass
        return "Failed"

    try:
        with transaction.atomic():
            order = Order.objects.get(merchant_uid=merchant_uid)
            
            # Check amount match (approve_response['amount']['total'])
            approved_amount = approve_response.get('amount', {}).get('total')

            Payment.objects.create(
                order=order,
                imp_uid=tid, # Use TID as imp_uid since we are using Kakao
                amount=approved_amount,
                status='paid',
                response_json=approve_response
            )

            if approved_amount == order.total_amount:
                order.status = 'PAID'
                order.save()
                
                Basket.objects.filter(user=order.user).delete()
                
                logger.info(f"[Payment Success] Order: {merchant_uid} verified and saved.")
            else:
                order.status = 'FAILED' # Or 'MISMATCH'
                order.save()
                logger.warning(f"[Payment Mismatch] Order: {merchant_uid}, Approved: {approved_amount} vs Order: {order.total_amount}")

    except Order.DoesNotExist:
        logger.error(f"[Payment Critical Error] Order not found for {merchant_uid}")
        return "Order Not Found"
    except Exception as e:
        logger.error(f"[Payment Critical Error] {e}")
        return f"Error: {e}"
        
    return "Success"
