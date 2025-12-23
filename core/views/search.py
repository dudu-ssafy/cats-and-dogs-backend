from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pgvector.django import CosineDistance
import os
import requests

# Import models
from core.models.board import Board
from core.models.shop import Product
from core.models.shorts import Shorts

class VectorSearchTestView(APIView):
    """
    Vector Similarity Search Test View
    GET /api/search/test/?query=...&model=...
    """
    def get(self, request):
        query_text = request.query_params.get('query', '')
        target_model = request.query_params.get('model', 'board') # board, pet, product, shorts, breed_knowledge

        if not query_text:
             return Response({"error": "Query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Generate embedding using SSAFY GMS (API Proxy)
        gms_key = os.environ.get('GMS_KEY')
        if not gms_key:
             return Response({"error": "GMS_KEY not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/embeddings"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {gms_key}"
            }
            payload = {
                "model": "text-embedding-3-small",
                "input": query_text
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status() # Raise error for bad status codes

            embedding = response.json()['data'][0]['embedding']
        except requests.exceptions.RequestException as e:
            return Response({"error": f"GMS API Error: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)
        except (KeyError, IndexError) as e:
             return Response({"error": f"Unexpected API Response format: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)

        # 2. Perform Similarity Search for each model
        # Shorts (5개)
        shorts_results = Shorts.objects.annotate(
            distance=CosineDistance('embedding', embedding)
        ).order_by('distance')[:5]

        # Board (5개)
        board_results = Board.objects.annotate(
            distance=CosineDistance('embedding', embedding)
        ).order_by('distance')[:5]

        # Product (4개)
        product_results = Product.objects.annotate(
            distance=CosineDistance('embedding', embedding)
        ).order_by('distance')[:4]

        # 3. Serialize results
        data = {
            "shorts": [],
            "boards": [],
            "products": []
        }

        for item in shorts_results:
            data['shorts'].append({
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "thumbnail_url": item.thumbnail_url,
                "video_url": item.video_url,
                "distance": item.distance
            })

        for item in board_results:
            data['boards'].append({
                "id": item.id,
                "category": item.category,
                "title": item.title,
                "author": item.author.nickname if item.author and hasattr(item.author, 'nickname') else (item.author.username if item.author else "익명"),
                "date": item.created_at.strftime('%Y-%m-%d'),
                "comments": getattr(item, 'comments_count', 0), # Need annotation or separate query if related_name exists
                "views": item.views,
                "distance": item.distance
            })

        for item in product_results:
            # Format price
            price = f"{item.base_price:,}원" if item.base_price else "가격미정"
            data['products'].append({
                "id": item.id,
                "name": item.title, # Frontend expects 'name'
                "title": item.title,
                "description": item.description,
                "price": price, 
                "img": item.images.first().image_url if item.images.exists() else None, # Frontend expects 'img'
                "image": item.images.first().image_url if item.images.exists() else None,
                "distance": item.distance
            })

        return Response({
            "query": query_text,
            "results": data
        })
