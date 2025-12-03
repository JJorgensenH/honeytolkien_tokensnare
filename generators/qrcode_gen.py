from .common import register_token
import qrcode

def generate_qrcode_honeytoken(server_url, output_file, description):
    token_data = register_token(
        server_url, 
        token_type="qrcode",
        description=description
    )
    
    tracking_url = token_data['tracking_url_link']

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    
    qr.add_data(tracking_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    img.save(output_file)