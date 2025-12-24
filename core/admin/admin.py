from django.contrib import admin
from core.models.pet import Pet
from core.models.board import Board
from core.models.shorts import Shorts, ShortsComment
from core.models.like import BoardLike, ShortsLike
from core.models.shop import Category, Product, ProductOption, ProductImage
from core.models.basket import Basket, BasketItem
from core.models.order import Order, OrderItem
from core.models.payment import Payment
from core.models.chat import ChatSession
from django.conf import settings
from django import forms
from core.tasks import process_shorts_video
from django.db import transaction
import os
import logging
logger = logging.getLogger('task')

class ShortsAdminForm(forms.ModelForm):
    video_file = forms.FileField(required=False, label="비디오 파일 업로드")

    class Meta:
        model = Shorts
        fields = '__all__'

@admin.register(Shorts)
class ShortsAdmin(admin.ModelAdmin):
    form = ShortsAdminForm
    list_display = ('id', 'title', 'author', 'created_at')
    list_display_links = ('id', 'title')
    search_fields = ('title', 'description', 'author__email')
    list_filter = ('created_at',)

    def save_model(self, request, obj, form, change):
        video_file = form.cleaned_data.get('video_file')
        super().save_model(request, obj, form, change)

        if video_file:
            logger.info(f"[Admin] Processing video for Shorts {obj.id}")
            # 파일을 임시 저장 후 Celery 태스크 실행
            temp_path = os.path.join(settings.BASE_DIR, 'temp_shorts', f"pending_{obj.id}_{video_file.name}")
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            with open(temp_path, 'wb+') as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)
            
            # 중요: DB 트랜잭션이 커밋된 후에 Celery 태스크를 실행하도록 보장
            transaction.on_commit(lambda: process_shorts_video.delay(obj.id, temp_path, video_file.name))

@admin.register(ShortsComment)
class ShortsCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'shorts', 'author', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__email')

@admin.register(ShortsLike)
class ShortsLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'shorts', 'created_at')
    list_filter = ('created_at',)

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'views', 'created_at')
    search_fields = ('title', 'content', 'author__email')

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at',)

from core.services.util import upload_to_gcs

class ProductImageForm(forms.ModelForm):
    image_upload = forms.FileField(required=False, label="이미지 파일 업로드")

    class Meta:
        model = ProductImage
        fields = '__all__'

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    form = ProductImageForm
    extra = 1

class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 1

class ProductAdminForm(forms.ModelForm):
    sumnail_upload = forms.FileField(required=False, label="상세 이미지(썸네일) 업로드")

    class Meta:
        model = Product
        fields = '__all__'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('id', 'title', 'category', 'base_price', 'is_sale', 'created_at')
    list_filter = ('category', 'is_sale', 'created_at')
    search_fields = ('title', 'description')
    inlines = [ProductImageInline, ProductOptionInline]

    def save_model(self, request, obj, form, change):
        # 상품 메인/상세 이미지 업로드 처리
        sumnail = form.cleaned_data.get('sumnail_upload')
        if sumnail:
            try:
                # GCS 업로드
                url = upload_to_gcs(sumnail, f"products/detail_{obj.id}_{sumnail.name}")
                obj.detail_image_url = url
            except Exception as e:
                logger.error(f"Failed to upload product thumbnail: {e}")
        
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        # 인라인 이미지 업로드 처리
        if formset.model == ProductImage:
            instances = formset.save(commit=False)
            
            # formset.forms를 순회하며 파일 업로드 처리
            for i, inline_form in enumerate(formset.forms):
                if not inline_form.is_valid():
                    continue
                
                # 삭제가 아니고, 변경사항이 있는 경우
                if inline_form.cleaned_data and not inline_form.cleaned_data.get('DELETE'):
                    image_file = inline_form.cleaned_data.get('image_upload')
                    if image_file:
                        try:
                            # Product ID가 아직 없을 수 있으므로(새 생성), form.instance.id 또는 임시 ID 사용
                            product_id = form.instance.id if form.instance.id else 'temp'
                            url = upload_to_gcs(image_file, f"products/{product_id}/imgs_{image_file.name}")
                            inline_form.instance.image_url = url
                        except Exception as e:
                            logger.error(f"Failed to upload inline image: {e}")
            
            formset.save()
        else:
            formset.save()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        
        # 이미지 업로드 후 Gemini 분석 태스크 실행 (트랜잭션 커밋 후)
        # 썸네일 업로드 확인
        sumnail = form.cleaned_data.get('sumnail_upload')
        has_thumbnail = bool(sumnail or form.instance.detail_image_url)
        
        # 인라인 이미지 업로드 확인
        has_inline_images = form.instance.images.exists() 

        if has_thumbnail or has_inline_images:
            from core.tasks import process_product_analysis
            transaction.on_commit(lambda: process_product_analysis.delay(form.instance.id))

admin.site.register(Basket)
admin.site.register(BasketItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(BoardLike)
