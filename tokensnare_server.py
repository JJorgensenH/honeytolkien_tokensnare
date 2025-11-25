import argparse
from flask import Flask, Response, request, jsonify
from datetime import datetime, timezone, timedelta
import logging
import json
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Desactivar logs de acceso
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
BUENOS_AIRES_TZ = timezone(timedelta(hours=-3))

# pixel transparente 1x1
TRANSPARENT_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
    b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)

# Base de datos simple (en memoria + persistencia JSON)
tokens_db = {}
hits_db = []

DB_FILE = Path("tokensnare_db.json")

def load_database():
    global tokens_db, hits_db
    if DB_FILE.exists():
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            tokens_db = data.get('tokens', {})
            hits_db = data.get('hits', [])


def save_database():
    with open(DB_FILE, 'w') as f:
        json.dump({
            'tokens': tokens_db,
            'hits': hits_db
        }, f, indent=2)

def generate_token_id(data_string):
    return hashlib.sha256(data_string.encode()).hexdigest()[:16]

def get_timestamp():
    return datetime.now(BUENOS_AIRES_TZ).isoformat()

def get_timestamp_human():
    return datetime.now(BUENOS_AIRES_TZ).strftime("%Y-%m-%d %H:%M:%S")

def construct_response_with_urls(token_id, record):
    """
    Reconstruye las URLs de tracking para responder al cliente.
    La CLI las necesita.
    """
    base_url = request.host_url.rstrip('/')
    response_data = record.copy()
    response_data['tracking_url_image'] = f"{base_url}/image/{token_id}.png"
    response_data['tracking_url_link'] = f"{base_url}/link/{token_id}"
    return response_data

def log_print(message):
    """
    Imprime en consola con formato estándar y hora de Buenos Aires.
    Formato: [dd/Mes/YYYY:HH:MM:SS] Mensaje
    """
    timestamp = get_timestamp_human()
    print(f"[{timestamp}] {message}")

# ============================================================================
# ENDPOINTS DE LA API (ADMIN)
# ============================================================================
@app.route("/api/tokens", methods=['POST'])
def register_honeytoken():
    data = request.get_json()
    
    if not data or 'type' not in data:
        return jsonify({"error": "Campo 'type' requerido"}), 400
    
    current_time = get_timestamp()

    ht_type = data['type']
    ht_desc = data.get('description') or "Sin descripción"
    token_id = generate_token_id(ht_type + ht_desc + current_time)

    token_record = {
        'token': token_id,
        'type': ht_type,
        'description': ht_desc,
        'created_at': current_time,
        'hits': 0,
        'last_hit': None
    }
    tokens_db[token_id] = token_record
    save_database()

    log_print(f"Nuevo honeytoken registrado | ID: {token_id} | Tipo: {ht_type}")

    return jsonify(construct_response_with_urls(token_id, token_record)), 201


@app.route("/api/tokens", methods=['GET'])
def list_honeytokens():
    output_list = list(tokens_db.values())
    return jsonify({'tokens': output_list, 'total': len(output_list)})

@app.route("/api/tokens/<token>", methods=['GET'])
def get_honeytoken_info(token):
    if token not in tokens_db:
        return jsonify({"error": "Honeytoken no encontrado"}), 404

    ht_info = tokens_db[token].copy()
    ht_info['hit_history'] = [
        hit for hit in hits_db if hit['token'] == token
    ]

    return jsonify(ht_info)


@app.route("/api/tokens/<token>", methods=['DELETE'])
def delete_honeytoken(token):
    """Elimina un honeytoken específico y sus hits asociados."""
    global hits_db
    if token not in tokens_db:
        return jsonify({"error": "Honeytoken no encontrado"}), 404
    
    del tokens_db[token]
    hits_db = [hit for hit in hits_db if hit['token'] != token]
    save_database()

    log_print(f"Honeytoken eliminado | ID: {token}")

    return jsonify({"message": f"Honeytoken {token} eliminado"}), 200


@app.route("/api/tokens/all", methods=['DELETE'])
def delete_all():
    """Elimina TODOS los honeytokens y hits. Útil para reiniciar."""
    global tokens_db, hits_db
    tokens_db.clear()
    hits_db.clear()
    save_database()

    log_print(f"DB Reset")
    return jsonify({"message": "DB Reset"}), 200


# ============================================================================
# TRACKING
# ============================================================================

def _register_hit(token: str):
    """
    Función helper interna.
    Registra un hit para un honeytoken, actualiza la DB y guarda en disco.
    """
    ts_iso = get_timestamp()
    
    ip = request.headers.getlist("X-Forwarded-For")[0] if request.headers.getlist("X-Forwarded-For") else request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Registra el hit
    hit_record = {
        'token': token,
        'timestamp': ts_iso,
        'ip': ip,
        'user_agent': user_agent,
        'headers': dict(request.headers)
    }
    
    hits_db.append(hit_record)

    # Alerta
    if token in tokens_db:
        tokens_db[token]['hits'] += 1
        tokens_db[token]['last_hit'] = ts_iso
        token_type = tokens_db[token]['type']
        description = tokens_db[token]['description']
        log_print(f"ALERTA HIT | ID: {token} | Tipo: {token_type} | Descripción: {description} | IP: {ip} | UA: {user_agent}")

    else:
        log_print(f"ALERTA HIT NO ESPERADO | IP: {ip} | UA: {user_agent}")
    save_database()


@app.route("/image/<token>.png", methods=['GET', 'OPTIONS'])
def image_hit(token):
    """
    Endpoint de tracking (IMAGEN). 
    Se activa cuando se carga la imagen.
    Registra el hit y retorna una imagen transparente.
    """
    if request.method == 'OPTIONS':
        return ('', 204)
    _register_hit(token)
    return Response(TRANSPARENT_PNG, mimetype="image/png")


@app.route("/link/<token>", methods=['GET', 'OPTIONS'])
def link_hit(token):
    """
    Endpoint de tracking (LINK). 
    Se activa cuando se accede al link.
    Registra el hit y retorna '204 No Content'
    Útil por si no se necesita retornar una imagen.
    """
    if request.method == 'OPTIONS':
        return ('', 204)
    _register_hit(token)
    return ('', 204)


@app.route("/", methods=['GET'])
def index():
    """Página de información del servidor."""
    return jsonify({
        'service': 'TokenSnare', 
        'active_tokens': len(tokens_db), 
        'hits': len(hits_db)
    })


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="TokenSnare Alert Server - Servidor de honeytokens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Endpoints:
  POST   /api/tokens          - Registrar
  GET    /api/tokens          - Listar
  GET    /api/tokens/<token>  - Detalles
  DELETE /api/tokens/<token>  - Borrar uno
  DELETE /api/tokens/all      - Borrar todo
  
  GET    /image/<token>.png   - Tracking (Imagen)
  GET    /link/<token>        - Tracking (Link)

La base de datos se guarda en: tokensnare_db.json
        """
    )
    
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host del servidor (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Puerto del servidor (default: 5000)')
    
    args = parser.parse_args()
    
    # Cargar base de datos
    load_database()
    
    print("=" * 60)
    print("TokenSnare Alert Server")
    print("=" * 60)
    print(f"Servidor corriendo en: http://{args.host}:{args.port}")
    print(f"Honeytokens registrados hasta el momento: {len(tokens_db)}")
    print("=" * 60)
    
    # Iniciar servidor
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()