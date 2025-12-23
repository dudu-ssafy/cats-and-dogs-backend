import os
import requests

def process_embedding(title, content):
    gms_key = os.environ.get('GMS_KEY')
    url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {gms_key}"
    }
    payload = {
        "model": "text-embedding-3-small",
        "input": f"Title: {title}\nSummary: {title}\nContent: {content}"
    }

    response = requests.post(url, json=payload, headers=headers)
    embedding = response.json()['data'][0]['embedding']

    return embedding

def upload_to_gcs(file_obj, destination_blob_name):
    """
    파일 객체를 GCS에 업로드하고 공개 URL을 반환합니다.
    """
    from google.cloud import storage
    from django.conf import settings
    
    client = storage.Client.from_service_account_json(settings.GS_CREDENTIALS)
    bucket = client.bucket(settings.GS_BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)
    
    # 파일 포인터 위치 초기화
    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)
        
    blob.upload_from_file(file_obj, content_type=file_obj.content_type if hasattr(file_obj, 'content_type') else None)
    return blob.public_url
