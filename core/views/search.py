from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import F
from pgvector.django import CosineDistance
import numpy as np
import os
import requests

# Import models
from core.models.board import Board
from core.models.pet import Pet, BreedKnowledge
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
            print('embedding 결과:', embedding)
        except requests.exceptions.RequestException as e:
            return Response({"error": f"GMS API Error: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)
        except (KeyError, IndexError) as e:
             return Response({"error": f"Unexpected API Response format: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)

        # 2. Select the model
        model_map = {
            'board': Board,
            'pet': BreedKnowledge,
            'product': Product,
            'shorts': Shorts
        }
        
        ModelClass = model_map.get(target_model.lower())
        if not ModelClass:
            return Response(
                {"error": f"Invalid model. Available models: {', '.join(model_map.keys())}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Perform Similarity Search using Cosine Distance
        # Order by distance (ascending) -> most similar first
        results = ModelClass.objects.annotate(
            distance=CosineDistance('embedding', embedding)
        ).order_by('distance')[:5]

        # 4. Serialize results
        # 4. Serialize results
        data = []
        if target_model == 'pet': # Handle BreedKnowledge results
            for item in results:
                data.append({
                    "id": item.id,
                    "breed": item.breed.name,
                    "title": item.title,
                    "content": item.content,
                    "distance": item.distance
                })
        elif target_model == 'board':
            for item in results:
                data.append({
                    "id": item.id,
                    "title": item.title,
                    "content": item.content,
                    "distance": item.distance
                })
        elif target_model == 'product':
             for item in results:
                data.append({
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "price": item.base_price,
                    "distance": item.distance
                })
        elif target_model == 'shorts':
             for item in results:
                data.append({
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "distance": item.distance
                })
        else:
             # Fallback for generic or unknown models
             for item in results:
                item_data = {"id": getattr(item, 'id', None), "distance": item.distance}
                if hasattr(item, 'title'): item_data['title'] = item.title
                if hasattr(item, 'name'): item_data['name'] = item.name
                data.append(item_data)

        return Response({
            "query": query_text,
            "target_model": target_model,
            "results": data
        })
