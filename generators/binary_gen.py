from .common import register_token

# Placeholder para la URL en el binario
PLACEHOLDER = b"PLACEHOLDER_URL_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"


def generate_binary_honeytoken(server_url, output_file, platform, description):
    """
    Genera un binario que realiza el get hacia la URI, parcheando una plantilla pre-compilada.
    """

    if platform == "windows":
        template_path = f"binary_template/template_win.exe"
    elif platform == "linux":
        template_path = f"binary_template/template_linux"
    else:
        raise ValueError("Las plataformas soportadas son windows y linux.")

    token_data = register_token(
        server_url,
        token_type="binary",
        description=description
    )

    tracking_url = token_data['tracking_url_link']

    url_bytes = tracking_url.encode('utf-8')

    # Validación: La URL no puede ser más larga que el placeholder
    if len(url_bytes) > len(PLACEHOLDER):
        raise ValueError("La URL generada es demasiado larga para el placeholder del binario.")

    with open(template_path, "rb") as f:
        binary_data = f.read()

    if PLACEHOLDER not in binary_data:
        raise Exception("Error: No se encontró el placeholder en el binario.")

    padded_url = url_bytes + b'\x00' * (len(PLACEHOLDER) - len(url_bytes))

    new_binary_data = binary_data.replace(PLACEHOLDER, padded_url)

    with open(output_file, "wb") as f:
        f.write(new_binary_data)
