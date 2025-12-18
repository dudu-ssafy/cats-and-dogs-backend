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
