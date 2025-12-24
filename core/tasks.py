import logging
from celery import shared_task
from django.db import transaction
from .models import Order, Payment, Basket
from .services.payment import PaymentService
from google.cloud import storage
from core.models import User
from django.conf import settings
import os

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

@shared_task(bind=True, max_retries=3)
def process_shorts_video(self, shorts_id, local_file_path, original_filename):
    """
    쇼츠 비디오를 처리합니다: GCS 업로드, 썸네일 추출, Gemini를 이용한 설명 생성, 임베딩 생성.
    """
    from core.models.shorts import Shorts
    from core.services.util import process_embedding
    import subprocess
    import imageio_ffmpeg
    import io
    import os
    
    logger = logging.getLogger('task')
    logger.info(f"[Task Start] Processing video for Shorts {shorts_id}")

    try:
        try:
            shorts = Shorts.objects.get(id=shorts_id)
        except Shorts.DoesNotExist:
            # 트랜잭션 커밋 대기를 위해 재시도
            logger.warning(f"Shorts {shorts_id} not found, retrying... (Attempt {self.request.retries})")
            raise self.retry(countdown=2)

        # 0. 비디오 압축 및 최적화 (FFmpeg 사용)
        # MoviePy 버전 이슈로 인해 더 안정적인 FFmpeg subprocess 호출 방식으로 전환합니다.
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        compressed_path = local_file_path + "_compressed.mp4"
        thumb_path = local_file_path + "_thumb.jpg"

        logger.info(f"Processing video with FFmpeg: {local_file_path}")

        # 1. Gemini 분석용 극강의 소형화 (너비 160px, 1fps, 50k 비트레이트)
        compress_cmd = [
            ffmpeg_exe, '-i', local_file_path,
            '-t', '10', 
            '-vf', "scale='min(160,iw)':-2,fps=1",
            '-vcodec', 'libx264', '-b:v', '50k',
            '-preset', 'ultrafast',
            '-movflags', '+faststart',
            '-an', '-y', compressed_path
        ]

        result = subprocess.run(compress_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg compression failed: {result.stderr}")
            raise Exception(f"FFmpeg compression failed: {result.stderr[:200]}")

        # 압축된 파일 크기 로그 기록 (디버깅용)
        if os.path.exists(compressed_path):
            file_size_kb = os.path.getsize(compressed_path) / 1024
            logger.info(f"Compressed video size for analysis: {file_size_kb:.2f} KB")

        # 2. 썸네일 추출 (0초 지점)
        thumb_cmd = [
            ffmpeg_exe, '-i', local_file_path,
            '-ss', '00:00:00', '-vframes', '1',
            '-q:v', '2', '-y', thumb_path
        ]
        
        result = subprocess.run(thumb_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg thumbnail failed: {result.stderr}")
            raise Exception(f"FFmpeg thumbnail extraction failed")

        with open(thumb_path, 'rb') as f:
            thumb_io = io.BytesIO(f.read())
        
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

        # 1. GCS 업로드 (원본 비디오 및 썸네일)
        storage_client = storage.Client.from_service_account_json(settings.GS_CREDENTIALS)
        bucket = storage_client.bucket(settings.GS_BUCKET_NAME)

        # 비디오 업로드 (원본 파일 업로드)
        video_blob = bucket.blob(f"shorts/video_{shorts_id}/{original_filename}")
        video_blob.upload_from_filename(local_file_path)
        video_url = video_blob.public_url

        # 썸네일 업로드
        thumb_blob = bucket.blob(f"shorts/thumb_{shorts_id}/thumbnail.jpg")
        thumb_blob.upload_from_file(thumb_io, content_type='image/jpeg')
        thumbnail_url = thumb_blob.public_url

        # 압축된 비디오 업로드
        compress_blob = bucket.blob(f"shorts/video_{shorts_id}/{original_filename}_compressed.mp4")
        compress_blob.upload_from_filename(compressed_path)
        compressed_url = compress_blob.public_url


        # 2. Gemini를 이용한 제목/설명 생성 (FastAPI 스타일 참조)
        gms_key = os.environ.get('GMS_KEY')
        title = shorts.title
        description = shorts.description

        if gms_key and (not title or not description):
            from google import genai
            from google.genai.types import Part

            # FastAPI 서버와 동일하게 GMS 프록시를 이용한 설정
            client = genai.Client(
                api_key=gms_key,
                http_options={"base_url": "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com"}
            )
            

            prompt = '''
            반려동물 영상 분석가이자 SEO 전문가로서 임베딩을 위한 글을 쓸꺼야.
            다음 url 영상을 분석해 JSON 형식으로만 응답해줘.

            [응답 JSON 형식]
            {
              "title": "영상의 핵심 내용을 요약한 제목 (20자 이내)",
              "description": "동물 특징, 배경, 행동을 포함한 상세 설명 (3-5문장)",
              "tags": ["검색용", "핵심", "키워드", "5-15개"]
            }
            
            부연 설명 없이 JSON 코드 블록만 출력하고 모든 내용은 한국어로 작성해줘.
            '''

            try:
                # SDK v2 스타일 호출
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[
                        Part.from_uri(file_uri=compressed_url, mime_type="video/mp4"),
                        prompt
                    ]
                )

                import json
                # JSON 코드 블록 제거 및 파싱
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                res_data = json.loads(clean_text)
                print('res_data:', res_data)
                # 제목 추출 및 200자 제한
                if not title:
                    title = res_data.get('title', f"반려동물 쇼츠 {shorts_id}")[:100]
                
                # 설명 및 태그 합치기
                description = res_data.get('description', "귀여운 반려동물 영상입니다.")
                tags = res_data.get('tags', [])
                if tags:
                    description += f"\n\nTags: {', '.join(tags)}"

                
            except Exception as e:
                logger.error(f"Gemini Processing Error: {e}")
            
            finally:
                # GCS에 업로드된 분석용 임시 파일(압축본) 삭제
                try:
                    if 'compress_blob' in locals():
                        compress_blob.delete()
                        logger.info("Deleted temp compressed video from GCS")
                except Exception as e:
                    logger.warning(f"Failed to delete temp GCS file: {e}")


        # 4. 임베딩 생성
        embedding = process_embedding(title, description)

        # 5. DB 업데이트
        shorts.video_url = video_url
        shorts.thumbnail_url = thumbnail_url
        shorts.title = title
        shorts.description = description
        shorts.embedding = embedding
        shorts.save()

        if os.path.exists(local_file_path):
            os.remove(local_file_path)
        if 'compressed_path' in locals() and os.path.exists(compressed_path):
            os.remove(compressed_path)

        logger.info(f"[Task Success] Shorts {shorts_id} processed successfully")
        return f"Success: {shorts_id}"

    except Exception as e:
        logger.error(f"[Task Failed] Shorts {shorts_id}: {str(e)}")
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
        if 'compressed_path' in locals() and os.path.exists(compressed_path):
            os.remove(compressed_path)
        return f"Error: {str(e)}"


@shared_task
def upload_user_image_to_gcs(user_id, local_file_path, original_filename):
    """
    구글 클라우드에 사용자 프로필 이미지를 업로드합니다.
    """
    logger = logging.getLogger('task')
    logger.info(f"[Task Start] Uploading user image to GCS for user {user_id}")

    client = storage.Client.from_service_account_json(settings.GS_CREDENTIALS)
    bucket = client.bucket(settings.GS_BUCKET_NAME)
    blob_name = f"profiles/user_{user_id}/{original_filename}"
    blob = bucket.blob(blob_name)
    
    blob.upload_from_filename(local_file_path)
    ser = User.objects.get(id=user_id)
    ser.profile_image = blob.public_url # 공개 URL 저장
    ser.save()

    try:
        os.remove(local_file_path)
        return f"Upload Success: {ser.profile_image}"
    except Exception as e:
        return f"Delete File Failed: {str(e)}"


@shared_task(bind=True, max_retries=3)
def process_product_analysis(self, product_id):
    """
    상품 이미지를 분석하여 설명을 생성하고 임베딩을 저장합니다.
    """
    from core.models.shop import Product
    from core.services.util import process_embedding
    import base64
    import requests
    import json
    from google import genai
    from google.genai.types import Part

    logger = logging.getLogger('task')
    logger.info(f"[Task Start] Analyzing product {product_id}")

    try:
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            logger.warning(f"Product {product_id} not found, retrying...")
            raise self.retry(countdown=2)

        gms_key = os.environ.get('GMS_KEY')
        
        # 1. Gemini Description Generation
        # 이미지 소스 수집: 메인 상세 이미지 + 추가 이미지들
        image_urls = []
        if product.detail_image_url:
            image_urls.append(product.detail_image_url)
        
        # 인라인 이미지들 추가
        for img in product.images.all():
            if img.image_url:
                image_urls.append(img.image_url)

        if gms_key and image_urls and not product.description:
            try:
                image_parts = []
                logger.info(f"Preparing {len(image_urls)} image URIs for analysis...")

                for url in image_urls:
                    # Simple mime type detection based on extension
                    mime_type = "image/jpeg"
                    if url.lower().endswith(".png"):
                        mime_type = "image/png"
                    elif url.lower().endswith(".webp"):
                        mime_type = "image/webp"
                    
                    image_parts.append(Part.from_uri(file_uri=url, mime_type=mime_type))

                if not image_parts:
                    logger.warning("No valid images found for analysis.")
                    raise Exception("No valid images")

                client = genai.Client(
                    api_key=gms_key,
                    http_options={"base_url": "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com"}
                )

                prompt = """
                반려동물 용품 쇼핑몰의 SEO 전문가로서 제공된 상품 이미지들을 종합적으로 분석해줘.
                메인 이미지와 세부 컷들을 모두 참고하여 JSON 형식으로 응답해:
                {
                    "description": "상품의 특징, 소재, 디자인 디테일, 반려동물에게 좋은 점을 포함한 풍부한 상세 설명 (3-5문장)",
                    "tags": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]
                }
                JSON 코드 블록만 출력해.
                """

                contents = image_parts + [prompt]

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents
                )
                
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                res_data = json.loads(clean_text)
                
                description = res_data.get('description', '')
                tags = res_data.get('tags', [])
                
                if tags:
                    description += f"\n\nTags: {', '.join(tags)}"
                
                product.description = description
                logger.info(f"Generated description for Product {product_id} with {len(image_parts)} images")

            except Exception as e:
                logger.error(f"Gemini Analysis Failed for Product {product_id}: {e}")

        # 2. Embedding Generation
        if product.title and product.description:
            try:
                embedding = process_embedding(product.title, product.description)
                product.embedding = embedding
                logger.info(f"Generated embedding for Product {product_id}")
            except Exception as e:
                logger.error(f"Embedding Generation Failed for Product {product_id}: {e}")

        product.save()
        return f"Success: {product_id}"

    except Exception as e:
        logger.error(f"[Task Failed] Product {product_id}: {e}")
        return f"Error: {e}"
