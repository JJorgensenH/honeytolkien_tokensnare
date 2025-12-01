import requests
import sys
from random import randint
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

def register_token(server_url, token_type, description, metadata=None):
    """
    Registra un token en el servidor y retorna el diccionario con los datos (IDs y URLs).
    Si falla, maneja el error y termina la ejecución o retorna None.
    """
    # Aseguramos que no haya doble slash o falte http
    if not server_url.startswith("http"):
        server_url = f"http://{server_url}"
    
    api_url = f"{server_url.rstrip('/')}/api/tokens"

    load_dotenv()
    api_key = os.environ.get("API_KEY", None)
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    payload = {
        "type": token_type,
        "description": description,
        "metadata": metadata or {}
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error conectando con el servidor: {e}")
        exit(1)


def random_creation_date():
    """Genera fecha de creación aleatoria en 2025."""
    now = datetime.now(timezone.utc)
    start_of_2025 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    
    time_diff = (now - start_of_2025).total_seconds()
    random_seconds = randint(0, int(time_diff))
    creation_time = start_of_2025 + timedelta(seconds=random_seconds)
    
    return creation_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def random_modification_date(creation_timestamp):
    """Genera fecha de modificación posterior a creación."""
    now = datetime.now(timezone.utc)
    creation_time = datetime.fromisoformat(creation_timestamp.replace('Z', '+00:00'))
    
    time_diff = (now - creation_time).total_seconds()
    random_seconds = randint(0, int(time_diff))
    modified_time = creation_time + timedelta(seconds=random_seconds)
    
    return modified_time.strftime('%Y-%m-%dT%H:%M:%SZ')