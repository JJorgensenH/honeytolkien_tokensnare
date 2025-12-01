from pypdf import PdfWriter, PageObject
from pypdf.generic import DictionaryObject, NameObject, TextStringObject, ArrayObject, NumberObject
from .common import register_token

def generate_pdf_honeytoken(server_url, output_file, description, title=None, author=None, content=None):
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

    metadata = {}
    if title:
        metadata['/Title'] = title
    if author:
        metadata['/Author'] = author
    
    if metadata:
        writer.add_metadata(metadata)

    if content:
        # Add a text annotation showing the content
        annotation = DictionaryObject({
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/FreeText"),
            NameObject("/Rect"): ArrayObject([
                NumberObject(50), NumberObject(750), NumberObject(500), NumberObject(780)
            ]),
            NameObject("/Contents"): TextStringObject(content),
            NameObject("/F"): NumberObject(4) # Flag for print/view
        })
        
        # Add the annotation to the page
        if "/Annots" not in page:
            page[NameObject("/Annots")] = ArrayObject()
        page[NameObject("/Annots")].append(annotation)

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