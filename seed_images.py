import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models.shop import Product, ProductImage

# Sample images (Cats and Dogs theme)
SAMPLE_IMAGES = [
    "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1583337130417-3346a1be7dee?auto=format&fit=crop&w=800&q=80", 
    "https://images.unsplash.com/photo-1592194996308-7b43878e84a6?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1543466835-00a7907e9de1?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1548681528-6a5c45b66b42?auto=format&fit=crop&w=800&q=80"
]

def seed_images():
    products = Product.objects.all()
    count = 0
    for product in products:
        if not product.images.exists():
            image_url = random.choice(SAMPLE_IMAGES)
            ProductImage.objects.create(
                product=product,
                image_url=image_url,
                is_main=True
            )
            print(f"Added image to {product.title}")
            count += 1
    
    print(f"Successfully added images to {count} products! ✨")

if __name__ == '__main__':
    seed_images()
