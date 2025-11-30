import argparse
from flask import Flask, Response, request, jsonify, render_template, send_file
from flask_httpauth import HTTPBasicAuth
from datetime import datetime, timezone, timedelta
import logging
import json
import os, textwrap
import hashlib
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Desactivar logs de acceso
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
auth = HTTPBasicAuth()
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

ADMIN_USER = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

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
# RUTAS DE ADMIN PARA VISUALIZACIÓN WEB
# ============================================================================
@auth.verify_password
def verify_password(username, password):

    if username == ADMIN_USER and password == ADMIN_PASSWORD:
        return username
    return None

@app.route("/tokens")
@app.route("/api/tokens", methods=['GET'])
@auth.login_required
def honeytokens_index():
    # In your Flask route:
    return render_template("tokens_index.html", tokens=tokens_db, hits_list=hits_db)

# Assuming tokens_db and hits_db are available globally

@app.route("/tokens/<token>", methods=['GET'])
@auth.login_required
def show_token_details(token):
    if token not in tokens_db:
        # If the token is not found, render a simple 404 page (or redirect)
        return render_template("404.html", error_message=f"Honeytoken '{token}' no encontrado"), 404

    # Get the token's base info
    ht_info = tokens_db[token].copy()
    
    # Filter the global hits_db to get only hits for this token
    hit_history = [
        hit for hit in hits_db if hit['token'] == token
    ]

    # Render the detail template
    return render_template(
        "token_detail.html", 
        token_data=ht_info, 
        hit_history=hit_history
    )

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
    return render_template("home.html", active_tokens=len(tokens_db), hits=len(hits_db))

# ============================================================================
# Sitio web demo
# ============================================================================
@app.route("/website_demo")
def honeybank():
    server_url = request.host_url.rstrip("/")
    return render_template("index.html.j2", server_url=server_url)

@app.route("/assets/styles.css")
def css():
    server_url = request.host_url.rstrip("/")
    css = render_template("styles.css.j2", server_url=server_url)
    response = Response(css, mimetype="text/css")
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.route("/assets/honey_logo.svg")
def logo():
    # Detectar posible clonación
    referer = request.headers.get("Referer")
    current_host = request.host  # Ej: honeybank.com

    if referer:
        try:
            parsed_ref = urlparse(referer)
            ref_host = parsed_ref.netloc  # Ej: h0neybank.com

            if ref_host and ref_host != current_host:
                token_id = generate_token_id("WEBSITE_CLONE_PROTECION_CSS")

                if token_id not in tokens_db:
                    tokens_db[token_id] = {
                        "token": token_id,
                        "type": "WEB_CLONE",
                        "description": f"Sitio clonado detectado desde {ref_host}",
                        "created_at": get_timestamp(),
                        "hits": 0,
                        "last_hit": None,
                    }
                else:
                    tokens_db[token_id]["description"] = (
                        f"Sitio clonado detectado desde {ref_host}"
                    )

                _register_hit(token_id)

        except Exception as e:
            log_print(f"Error parseando referer en logo: {e}")

    return send_file("assets/honey_logo.svg", mimetype="image/svg+xml")

@app.route("/api/callback", methods=["POST", "OPTIONS"])
def js_callback():
    if request.method == "OPTIONS":
        response = Response("", status=204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"

        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, X-Cloned-Domain, X-Cloned-Url, X-Screen-Res"
        )
        return response

    token_id = generate_token_id("WEBSITE_CLONE_PROTECTION_JS")

    if token_id not in tokens_db:
        tokens_db[token_id] = {
            "token": token_id,
            "type": "WEB_CLONE_JS",
            "description": "Sitio web clonado (Reporte JS)",
            "created_at": get_timestamp(),
            "hits": 0,
            "last_hit": None,
        }

    cloned_domain = request.headers.get("X-Cloned-Domain")
    if cloned_domain:
        tokens_db[token_id]["description"] = f"Sitio web clonado en: {cloned_domain}"

    _register_hit(token_id)

    response = jsonify({"status": "ok"})
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="TokenSnare Alert Server - Servidor de honeytokens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Endpoints:
            POST   /api/tokens          - Registrar
            GET    /api/tokens          - Listar
            GET    /api/tokens/<token>  - Detalles
            DELETE /api/tokens/<token>  - Borrar uno
            DELETE /api/tokens/all      - Borrar todo
            
            GET    /image/<token>.png   - Tracking (Imagen)
            GET    /link/<token>        - Tracking (Link)

            La base de datos se guarda en: tokensnare_db.json
        """)
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