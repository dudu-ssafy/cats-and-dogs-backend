import logging
from celery import shared_task
from django.db import transaction
from .models import Order, Payment, Basket
from .services.payment import PaymentService


@shared_task
def process_kakao_payment_approval(pg_token, tid, merchant_uid, partner_user_id):
    logger = logging.getLogger('payment')
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

@shared_task
def update_popular_boards_daily():
    """
    주행마다 실행되며 최근 24시간의 조회수를 합산하여 인기글을 선정합니다.
    데이터 부족 시 기존 인기글을 유지(Sticky)합니다.
    """
    from core.services.redis import RedisService
    from core.models.board import Board
    from django.db.models import F
    from datetime import datetime, timedelta
    logger = logging.getLogger('task')
    logger.info("[Task Start] Updating popular boards (Sliding Window + Sticky Fallback)")

    # 1. 직전 시간대의 조회수를 DB에 동기화
    # (매 시간 실행된다고 가정하면, 1시간 전 데이터를 합산)
    last_hour = datetime.now() - timedelta(hours=1)
    bucket_key = RedisService.get_hour_bucket_key(last_hour)
    
    # 2. 최근 24시간 슬라이딩 윈도우 기반 인기글 ID 추출
    top_ids = [str(bid) for bid in RedisService.get_popular_ids_sliding_window(hours=24, limit=10)]
    
    # 3. Fallback: 상위 10개가 안 채워질 경우 기존 인기글(Sticky)에서 보충
    if len(top_ids) < 10:
        existing_popular_ids = [str(bid) for bid in RedisService.get_cached_popular_board_ids()]
        for pid in existing_popular_ids:
            if pid not in top_ids:
                top_ids.append(pid)
                if len(top_ids) >= 10:
                    break

    # 4. 마지막 수단: 여전히 부족하면 DB 전체 누적 조회수 순으로 보충
    if len(top_ids) < 10:
        additional_needed = 10 - len(top_ids)
        fallback_boards = Board.objects.exclude(id__in=top_ids).order_by('-views', '-created_at')[:additional_needed]
        top_ids.extend([str(board.id) for board in fallback_boards])

    # 5. Redis 캐시에 최종 인기글 ID 목록 저장 (최대 10개)
    RedisService.cache_popular_board_ids(top_ids[:10])

    logger.info(f"[Task Success] Popular boards updated. Top 10: {top_ids[:10]}")
    return f"Success: {len(top_ids[:10])} boards cached"
