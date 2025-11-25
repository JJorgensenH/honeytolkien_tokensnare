from ebooklib import epub
from .common import register_token

def get_default_css():
    return """
    @namespace epub "http://www.idpf.org/2007/ops";
    body { font-family: serif; }
    h1 { text-align: left; }
    """

def generate_epub_honeytoken(server_url, output_file, title, author, description, content):
    """
    Crea un EPUB inyectando un pixel de tracking en el HTML.
    """
    token_data = register_token(
        server_url,
        token_type="epub",
        description=description
    )
    
    tracking_url_image = token_data['tracking_url_image']

    book = epub.EpubBook()

    book.set_title(title if title else "")
    book.set_language("es")
    if author: book.add_author(author)


    head_title = title if title else ""
    html_h1 = f"<h1>{title}</h1>" if title else ""
    html_content = f"<p>{content}</p>" if content else ""

    c1 = epub.EpubHtml(title="Introducción", file_name="chapter1.xhtml", lang="es")

    c1.content = f"""
    <html>
      <head>
        <title>{head_title}</title>
      </head>
      <body>
        {html_h1}
        {html_content}
        <div style="background-image:url('{tracking_url_image}'); width:1px; height:1px; position:absolute; left:-9999px;"></div>
      </body>
    </html>
    """
    
    book.add_item(c1)

    style_css = get_default_css()
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style_css)
    book.add_item(nav_css)
    
    # book.toc = (epub.Link("chapter1.xhtml", title, "intro"),)
    book.spine = [c1]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(output_file, book, {})