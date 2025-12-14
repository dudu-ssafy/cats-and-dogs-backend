from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.services.payment import PaymentService

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
