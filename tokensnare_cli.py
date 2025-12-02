#!/usr/bin/env python3
"""
TokenSnare CLI
Herramienta centralizada para generación de Honeytokens.
"""
import argparse
from pathlib import Path

from generators import generate_pdf_honeytoken, generate_binary_honeytoken, generate_epub_honeytoken, generate_xlsx_honeytoken, generate_docx_honeytoken, generate_qrcode_honeytoken

OUTPUT_FOLDER_NAME = "honeyTokens"
FILE_TYPE_SUPPORTED = ['pdf', 'epub', 'xlsx', 'docx', 'qrcode', 'binary']


def get_output_path(filename):
    folder = Path(OUTPUT_FOLDER_NAME)
    folder.mkdir(exist_ok=True)
    full_path = folder / filename
    return str(full_path)


def main():
    parser = argparse.ArgumentParser(
        description="TokenSnare CLI - Generador de Honeytokens"
    )

    # Parámetros Obligatorios
    parser.add_argument('--type', required=True, choices=FILE_TYPE_SUPPORTED,
                        help='Tipo de honeytoken a generar')

    parser.add_argument('--output', required=True,
                        help='Nombre del archivo de salida (se guardará en honeyTokens/)')

    # Argumentos Generales
    parser.add_argument('--server', default='http://127.0.0.1:5000',
                        help='URL del servidor de alertas (default: localhost:5000)')

    parser.add_argument('--description',
                        help='Descripción para identificar el honeytoken en el servidor')

    # Parámetros opcionales
    parser.add_argument('--title', default=None,
                        help='Título del documento')
    parser.add_argument('--author', default=None,
                        help='Autor del documento')
    parser.add_argument('--content', default=None,
                        help='Texto del documento')
    parser.add_argument('--platform', default='linux', choices=['windows', 'linux'],
                        help='Plataforma del binario (solo para tipo binary)')

    args = parser.parse_args()

    final_output_path = get_output_path(args.output)

    match args.type:
        case 'pdf':
            generate_pdf_honeytoken(
                server_url=args.server,
                output_file=final_output_path,
                description=args.description,
                title=args.title,
                author=args.author,
                content=args.content
            )
        case 'epub':
            generate_epub_honeytoken(
                server_url=args.server,
                output_file=final_output_path,
                title=args.title,
                author=args.author,
                description=args.description,
                content=args.content
            )
        case 'xlsx':
            generate_xlsx_honeytoken(
                server_url=args.server,
                output_file=final_output_path,
                description=args.description,
                title=args.title,
                author=args.author,
                content=args.content
            )
        case 'docx':
            generate_docx_honeytoken(
                server_url=args.server,
                output_file=final_output_path,
                description=args.description,
                title=args.title,
                author=args.author,
                content=args.content
            )
        case 'qrcode':
            generate_qrcode_honeytoken(
                server_url=args.server,
                output_file=final_output_path,
                description=args.description,
            )
        case 'binary':
            generate_binary_honeytoken(
                server_url=args.server,
                output_file=final_output_path,
                platform=args.platform,
                description=args.description
            )
        case _:
            print("Tipo no reconocido")


if __name__ == "__main__":
    main()
