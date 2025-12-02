# Este archivo expone las funciones principales del paquete
# para que puedan ser importadas directamente desde 'generators'

from .pdf_gen import generate_pdf_honeytoken
from .epub_gen import generate_epub_honeytoken
from .xlsx_gen import generate_xlsx_honeytoken
from .docx_gen import generate_docx_honeytoken
from .qrcode_gen import generate_qrcode_honeytoken
from .binary_gen import generate_binary_honeytoken

# A futuro agregarás aquí los otros:
# from .word_gen import generate_word_token