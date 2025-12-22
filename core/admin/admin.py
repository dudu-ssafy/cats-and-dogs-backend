from django.contrib import admin
from core.models.pet import Pet
from core.models.board import Board
from core.models.shorts import Shorts, ShortsComment
from core.models.like import BoardLike, ShortsLike
from core.models.shop import Category, Product, ProductOption
from core.models.basket import Basket, BasketItem
from core.models.order import Order, OrderItem
from core.models.payment import Payment
from core.models.chat import ChatSession

@admin.register(Shorts)
class ShortsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'created_at')
    list_display_links = ('id', 'title')
    search_fields = ('title', 'description', 'author__email')
    list_filter = ('created_at',)

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

# 추가적인 모델들도 필요한 경우 등록
admin.site.register(Pet)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductOption)
admin.site.register(Basket)
admin.site.register(BasketItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(BoardLike)
