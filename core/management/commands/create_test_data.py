from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models.shop import Category, Product, ProductOption, ProductImage
from core.models.cart import Basket, BasketItem
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = '상품, 옵션, 장바구니 테스트 데이터를 생성합니다.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('테스트 데이터 생성을 시작합니다...'))

        # 1. 사용자 생성
        self.stdout.write('사용자 생성 중...')
        users = self.create_users()
        self.stdout.write(self.style.SUCCESS(f'✓ {len(users)}명의 사용자 생성 완료'))

        # 2. 카테고리 생성
        self.stdout.write('카테고리 생성 중...')
        categories = self.create_categories()
        self.stdout.write(self.style.SUCCESS(f'✓ {len(categories)}개의 카테고리 생성 완료'))

        # 3. 상품 생성
        self.stdout.write('상품 생성 중...')
        products = self.create_products(categories)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(products)}개의 상품 생성 완료'))

        # 4. 상품 옵션 생성
        self.stdout.write('상품 옵션 생성 중...')
        options = self.create_product_options(products)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(options)}개의 상품 옵션 생성 완료'))

        # 5. 상품 이미지 생성
        self.stdout.write('상품 이미지 생성 중...')
        images = self.create_product_images(products)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(images)}개의 상품 이미지 생성 완료'))

        # 6. 장바구니 및 장바구니 아이템 생성
        self.stdout.write('장바구니 생성 중...')
        baskets = self.create_baskets_and_items(users, options)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(baskets)}개의 장바구니 생성 완료'))

        self.stdout.write(self.style.SUCCESS('\n모든 테스트 데이터 생성이 완료되었습니다! 🎉'))

    def create_users(self):
        """테스트 사용자 생성"""
        users_data = [
            {'username': 'testuser1', 'email': 'test1@example.com', 'password': 'password123'},
            {'username': 'testuser2', 'email': 'test2@example.com', 'password': 'password123'},
            {'username': 'testuser3', 'email': 'test3@example.com', 'password': 'password123'},
        ]
        
        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
            users.append(user)
        
        return users

    def create_categories(self):
        """상품 카테고리 생성"""
        category_names = [
            '상의',
            '하의',
            '아우터',
            '액세서리',
            '신발',
        ]
        
        categories = []
        for name in category_names:
            category, _ = Category.objects.get_or_create(name=name)
            categories.append(category)
        
        return categories

    def create_products(self, categories):
        """상품 생성"""
        products_data = [
            {
                'category': categories[0],  # 상의
                'title': '베이직 코튼 티셔츠',
                'description': '부드러운 코튼 소재의 베이직 티셔츠입니다. 데일리로 착용하기 좋으며, 다양한 스타일링이 가능합니다.',
                'base_price': 29000,
                'is_sale': True,
            },
            {
                'category': categories[0],  # 상의
                'title': '오버핏 맨투맨',
                'description': '편안한 오버핏 맨투맨입니다. 두툼한 원단으로 가을, 겨울에 착용하기 좋습니다.',
                'base_price': 45000,
                'is_sale': True,
            },
            {
                'category': categories[1],  # 하의
                'title': '슬림핏 청바지',
                'description': '슬림한 핏의 청바지입니다. 신축성이 좋아 활동하기 편안합니다.',
                'base_price': 59000,
                'is_sale': True,
            },
            {
                'category': categories[1],  # 하의
                'title': '와이드 슬랙스',
                'description': '트렌디한 와이드 핏의 슬랙스입니다. 정장 스타일부터 캐주얼까지 다양하게 연출 가능합니다.',
                'base_price': 49000,
                'is_sale': True,
            },
            {
                'category': categories[2],  # 아우터
                'title': '후드 집업 점퍼',
                'description': '실용적인 후드 집업 점퍼입니다. 가볍고 따뜻하여 봄, 가을 환절기에 착용하기 좋습니다.',
                'base_price': 89000,
                'is_sale': True,
            },
            {
                'category': categories[2],  # 아우터
                'title': '롱 패딩 코트',
                'description': '따뜻한 롱 패딩 코트입니다. 고급스러운 디자인과 뛰어난 보온성을 자랑합니다.',
                'base_price': 159000,
                'is_sale': False,
            },
            {
                'category': categories[3],  # 액세서리
                'title': '레더 크로스백',
                'description': '고급 레더 소재의 크로스백입니다. 심플하면서도 세련된 디자인이 특징입니다.',
                'base_price': 79000,
                'is_sale': True,
            },
            {
                'category': categories[4],  # 신발
                'title': '캔버스 스니커즈',
                'description': '편안한 캔버스 스니커즈입니다. 데일리 신발로 착용하기 좋습니다.',
                'base_price': 39000,
                'is_sale': True,
            },
        ]
        
        products = []
        for product_data in products_data:
            product, _ = Product.objects.get_or_create(
                title=product_data['title'],
                defaults=product_data
            )
            products.append(product)
        
        return products

    def create_product_options(self, products):
        """상품 옵션 생성"""
        options = []
        
        # 베이직 코튼 티셔츠 옵션
        colors = ['화이트', '블랙', '그레이', '네이비']
        sizes = ['S', 'M', 'L', 'XL']
        for color in colors:
            for size in sizes:
                option, _ = ProductOption.objects.get_or_create(
                    product=products[0],
                    name='색상-사이즈',
                    value=f'{color}-{size}',
                    defaults={
                        'additional_price': 0,
                        'stock': 50,
                    }
                )
                options.append(option)
        
        # 오버핏 맨투맨 옵션
        colors = ['블랙', '그레이', '베이지']
        sizes = ['M', 'L', 'XL']
        for color in colors:
            for size in sizes:
                option, _ = ProductOption.objects.get_or_create(
                    product=products[1],
                    name='색상-사이즈',
                    value=f'{color}-{size}',
                    defaults={
                        'additional_price': 0,
                        'stock': 30,
                    }
                )
                options.append(option)
        
        # 슬림핏 청바지 옵션
        sizes = ['28', '29', '30', '31', '32', '33', '34']
        for size in sizes:
            option, _ = ProductOption.objects.get_or_create(
                product=products[2],
                name='사이즈',
                value=size,
                defaults={
                    'additional_price': 0,
                    'stock': 20,
                }
            )
            options.append(option)
        
        # 와이드 슬랙스 옵션
        colors = ['블랙', '그레이', '베이지']
        sizes = ['S', 'M', 'L']
        for color in colors:
            for size in sizes:
                option, _ = ProductOption.objects.get_or_create(
                    product=products[3],
                    name='색상-사이즈',
                    value=f'{color}-{size}',
                    defaults={
                        'additional_price': 0,
                        'stock': 25,
                    }
                )
                options.append(option)
        
        # 후드 집업 점퍼 옵션
        colors = ['블랙', '네이비', '카키']
        sizes = ['M', 'L', 'XL']
        for color in colors:
            for size in sizes:
                option, _ = ProductOption.objects.get_or_create(
                    product=products[4],
                    name='색상-사이즈',
                    value=f'{color}-{size}',
                    defaults={
                        'additional_price': 0,
                        'stock': 15,
                    }
                )
                options.append(option)
        
        # 롱 패딩 코트 옵션
        colors = ['블랙', '베이지']
        sizes = ['S', 'M', 'L']
        for color in colors:
            for size in sizes:
                option, _ = ProductOption.objects.get_or_create(
                    product=products[5],
                    name='색상-사이즈',
                    value=f'{color}-{size}',
                    defaults={
                        'additional_price': 10000 if color == '베이지' else 0,
                        'stock': 10,
                    }
                )
                options.append(option)
        
        # 레더 크로스백 옵션
        colors = ['블랙', '브라운', '베이지']
        for color in colors:
            option, _ = ProductOption.objects.get_or_create(
                product=products[6],
                name='색상',
                value=color,
                defaults={
                    'additional_price': 5000 if color == '브라운' else 0,
                    'stock': 20,
                }
            )
            options.append(option)
        
        # 캔버스 스니커즈 옵션
        sizes = ['240', '245', '250', '255', '260', '265', '270', '275', '280']
        for size in sizes:
            option, _ = ProductOption.objects.get_or_create(
                product=products[7],
                name='사이즈',
                value=size,
                defaults={
                    'additional_price': 0,
                    'stock': 15,
                }
            )
            options.append(option)
        
        return options

    def create_product_images(self, products):
        """상품 이미지 생성"""
        images = []
        
        # 각 상품에 대해 2-3개의 이미지 추가
        image_data = [
            # 베이직 코튼 티셔츠
            [
                {'url': 'https://picsum.photos/800/800?random=1', 'is_main': True, 'order': 0},
                {'url': 'https://picsum.photos/800/800?random=2', 'is_main': False, 'order': 1},
            ],
            # 오버핏 맨투맨
            [
                {'url': 'https://picsum.photos/800/800?random=3', 'is_main': True, 'order': 0},
                {'url': 'https://picsum.photos/800/800?random=4', 'is_main': False, 'order': 1},
                {'url': 'https://picsum.photos/800/800?random=5', 'is_main': False, 'order': 2},
            ],
            # 슬림핏 청바지
            [
                {'url': 'https://picsum.photos/800/800?random=6', 'is_main': True, 'order': 0},
                {'url': 'https://picsum.photos/800/800?random=7', 'is_main': False, 'order': 1},
            ],
            # 와이드 슬랙스
            [
                {'url': 'https://picsum.photos/800/800?random=8', 'is_main': True, 'order': 0},
                {'url': 'https://picsum.photos/800/800?random=9', 'is_main': False, 'order': 1},
            ],
            # 후드 집업 점퍼
            [
                {'url': 'https://picsum.photos/800/800?random=10', 'is_main': True, 'order': 0},
                {'url': 'https://picsum.photos/800/800?random=11', 'is_main': False, 'order': 1},
                {'url': 'https://picsum.photos/800/800?random=12', 'is_main': False, 'order': 2},
            ],
            # 롱 패딩 코트
            [
                {'url': 'https://picsum.photos/800/800?random=13', 'is_main': True, 'order': 0},
                {'url': 'https://picsum.photos/800/800?random=14', 'is_main': False, 'order': 1},
            ],
            # 레더 크로스백
            [
                {'url': 'https://picsum.photos/800/800?random=15', 'is_main': True, 'order': 0},
                {'url': 'https://picsum.photos/800/800?random=16', 'is_main': False, 'order': 1},
            ],
            # 캔버스 스니커즈
            [
                {'url': 'https://picsum.photos/800/800?random=17', 'is_main': True, 'order': 0},
                {'url': 'https://picsum.photos/800/800?random=18', 'is_main': False, 'order': 1},
            ],
        ]
        
        for idx, product in enumerate(products):
            for img_data in image_data[idx]:
                image, _ = ProductImage.objects.get_or_create(
                    product=product,
                    image_url=img_data['url'],
                    defaults={
                        'is_main': img_data['is_main'],
                        'order': img_data['order'],
                    }
                )
                images.append(image)
        
        return images

    def create_baskets_and_items(self, users, options):
        """장바구니 및 장바구니 아이템 생성"""
        baskets = []
        
        # 각 사용자에 대해 장바구니 생성
        for user in users:
            basket, _ = Basket.objects.get_or_create(user=user)
            baskets.append(basket)
        
        # 사용자 1의 장바구니에 아이템 추가
        basket_items_user1 = [
            {'option': options[0], 'quantity': 2},  # 베이직 티셔츠 화이트-S
            {'option': options[5], 'quantity': 1},  # 베이직 티셔츠 블랙-M
            {'option': options[20], 'quantity': 1},  # 오버핏 맨투맨
        ]
        
        for item_data in basket_items_user1:
            option = item_data['option']
            price = option.product.base_price + option.additional_price
            BasketItem.objects.get_or_create(
                basket=baskets[0],
                option=option,
                defaults={
                    'product': option.product,
                    'quantity': item_data['quantity'],
                    'price_at_addition': Decimal(str(price)),
                }
            )
        
        # 사용자 2의 장바구니에 아이템 추가
        basket_items_user2 = [
            {'option': options[30], 'quantity': 1},  # 청바지
            {'option': options[40], 'quantity': 1},  # 슬랙스
            {'option': options[50], 'quantity': 1},  # 점퍼
        ]
        
        for item_data in basket_items_user2:
            option = item_data['option']
            price = option.product.base_price + option.additional_price
            BasketItem.objects.get_or_create(
                basket=baskets[1],
                option=option,
                defaults={
                    'product': option.product,
                    'quantity': item_data['quantity'],
                    'price_at_addition': Decimal(str(price)),
                }
            )
        
        # 사용자 3의 장바구니에 아이템 추가
        basket_items_user3 = [
            {'option': options[70], 'quantity': 1},  # 가방
            {'option': options[75], 'quantity': 2},  # 신발
        ]
        
        for item_data in basket_items_user3:
            option = item_data['option']
            price = option.product.base_price + option.additional_price
            BasketItem.objects.get_or_create(
                basket=baskets[2],
                option=option,
                defaults={
                    'product': option.product,
                    'quantity': item_data['quantity'],
                    'price_at_addition': Decimal(str(price)),
                }
            )
        
        return baskets
