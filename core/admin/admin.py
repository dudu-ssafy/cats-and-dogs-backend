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

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'base_price', 'is_sale', 'created_at')
    list_filter = ('category', 'is_sale', 'created_at')
    search_fields = ('title', 'description')
    inlines = [ProductImageInline, ProductOptionInline]

@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'name', 'value', 'stock')
    list_filter = ('product',)
    search_fields = ('product__title', 'name', 'value')
admin.site.register(Basket)
admin.site.register(BasketItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(BoardLike)
