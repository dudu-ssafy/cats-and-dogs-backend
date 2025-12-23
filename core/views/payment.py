from django.shortcuts import redirect
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from core.services.payment import PaymentService
from core.services.redis import RedisService

class PaymentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """
        주문 생성 (Checkout)
        - 장바구니 내용으로 주문을 생성하고 merchant_uid를 반환합니다.
        """
        try:
            order = PaymentService.create_order(request.user)
            return Response({
                'merchant_uid': order.merchant_uid,
                'amount': order.total_amount,
                'buyer_email': order.user.email,
                'buyer_name': getattr(order.user, 'username', 'Unknown')
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify(self, request):
        """
        결제 검증 (Verify)
        - 포트원 결제 완료 후 호출되어 결제를 검증하고 처리합니다.
        """
        merchant_uid = request.data.get('merchant_uid')
        imp_uid = request.data.get('imp_uid')
        amount = request.data.get('amount')

        if not merchant_uid or not imp_uid:
            return Response({'error': 'merchant_uid and imp_uid are required'}, status=status.HTTP_400_BAD_REQUEST)

        payment = PaymentService.verify_payment(merchant_uid, imp_uid, amount)

        if payment and payment.order.status == 'PAID':
            return Response({'status': 'success', 'message': 'Payment verified'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failed', 'message': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get', 'post'])
    def toss(self, request):
        print(PaymentService.toss_payment())
        return Response({'status': 'success', 'message': 'Payment verified'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        주문 상태 조회
        """
        merchant_uid = request.GET.get('merchant_uid')
        if not merchant_uid:
            return Response({'error': 'merchant_uid is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from core.models import Order
        try:
            order = Order.objects.get(merchant_uid=merchant_uid)
            return Response({
                'merchant_uid': order.merchant_uid,
                'status': order.status,
                'total_amount': order.total_amount
            }, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def kakao_ready(self, request):
        try:
             order = PaymentService.create_order(request.user)
        except ValueError as e:
            print(e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        response = PaymentService.kakao_payment_ready(order)
        if response and 'tid' in response:
            RedisService.set_payment_data(order.merchant_uid, {
                'tid': response['tid'],
                'merchant_uid': order.merchant_uid,
                'partner_user_id': str(order.user.id)
            })

        return Response(response, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def kakao_redirect(self, request):
        merchant_uid = request.GET.get('merchant_uid')
        pg_token = request.GET.get('pg_token')

        if not merchant_uid:
             return redirect(f"{settings.FRONTEND_URL}/payment/result?status=fail&error=no_merchant_uid")

        payment_data = RedisService.get_payment_data(merchant_uid)
        
        if not payment_data or not pg_token:
            return redirect(f"{settings.FRONTEND_URL}/payment/result?status=fail&merchant_uid={merchant_uid}&error=invalid_session")

        tid = payment_data.get('tid')
        partner_user_id = payment_data.get('partner_user_id')

        from core.tasks import process_kakao_payment_approval
        task = process_kakao_payment_approval.delay(pg_token, tid, merchant_uid, partner_user_id)

        # Redirect to frontend status page with task_id
        return redirect(f"{settings.FRONTEND_URL}/payment/result?status=processing&merchant_uid={merchant_uid}&task_id={task.id}")
