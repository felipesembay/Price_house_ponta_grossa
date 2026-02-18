import requests

API_URL = "http://localhost:8009/predict"

def prever_preco(payload):
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()
    return response.json()
