from pypdf import PdfWriter, PageObject
from pypdf.generic import DictionaryObject, NameObject, TextStringObject
from .common import register_token

def generate_pdf_honeytoken(server_url, output_file, description):
    """
    Genera un PDF con OpenAction hacia una URI.
    """    
    token_data = register_token(
        server_url, 
        token_type="pdf",
        description=description
    )
    
    tracking_url = token_data['tracking_url_link']

    writer = PdfWriter()
    page = PageObject.create_blank_page(width=612, height=792)
    writer.add_page(page)

    # Definimos la acción URI
    uri_action = DictionaryObject({
        NameObject("/S"): NameObject("/URI"),
        NameObject("/URI"): TextStringObject(tracking_url)
    })

    # Inyectar OpenAction en el Root del PDF
    writer._root_object.update({
        NameObject("/OpenAction"): uri_action
    })

    with open(output_file, "wb") as f:
        writer.write(f)