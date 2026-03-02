from io import StringIO
from typing_extensions import override  # for Python < 3.12

from markdown_backend import MarkdownBackend
from utils import prettify_html


class HTMLBackend(MarkdownBackend):
    def __init__(self, out, style_sheet='', pretty_print=False):
        self._storage = out
        self._out = StringIO()
        self._style_sheet = style_sheet
        self._pretty_print = pretty_print
        self._inside_par = False  # Acrescentei - Controlo de linhas
    #:

    def close(self):
        self._storage.write(
            prettify_html(self._out.getvalue())
                if self._pretty_print
                else self._out.getvalue()
            )
        self._out.close()
    #:

    @override
    def open_document(self, title=''):
        out = self._out
        out.write("""<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n <meta charset=\"UTF-8\">\n <meta http-equiv=\"X-UA-Compatible\" content=\"IE=edge\">\n <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n""")
        if title:
            out.write(f'<title>{title}</title>\n')
        if self._style_sheet:
            out.write(f'<link rel=\"stylesheet\" media=\"all\" type=\"text/css\" '
                      f'href=\"{self._style_sheet}\">\n')
        out.write('</head>\n<body>\n\n')
    #:

    @override
    def close_document(self):
        self._out.write('\n</body>\n</html>\n')
    #:

    @override
    def open_heading(self, level: int):
        self._out.write(f'<h{level}>')
    #:

    @override
    def close_heading(self, level: int):
        self._out.write(f'</h{level}>\n')
    #:

    @override
    def new_text_line(self, line: str):
        # self._out.write(line)
        self._out.write(self.process_inline(line))  # Acrescentei
    #:

    @override
    def open_par(self):
        self._out.write('<p>')
        self._inside_par = True # Acrescentei
    #:

    @override
    def close_par(self):
        self._out.write('</p>\n')
        self._inside_par = False    # Acrescentei
    #:



    @override
    def open_list(self):
        self._out.write('<ul>\n')
    #:

    @override
    def close_list(self):
        self._out.write('</ul>\n')
    #:

    @override
    def open_list_item(self) -> None:
        self._out.write(' <li>')
        self._inside_par = False  # Acrescentei - lista nunca adiciona <br>
    #:

    @override
    def close_list_item(self) -> None:
        self._out.write('</li>\n')
        self._inside_par = False  # Acrescentei
    #:

    """Acrescentei"""
    @override
    def open_ordered_list(self):
        self._out.write('<ol>\n')
    #:

    @override
    def close_ordered_list(self):
        self._out.write('</ol>\n')
    #:

    @override
    def new_par_line(self, line: str):
        # self._out.write(f'{line}')
        # Acrescentei v
        # Não é a primeira linha do parágrafo, adiciona <br> antes
        current = self._out.getvalue()
        if self._inside_par and not current.endswith('<p>'):
            self._out.write('<br>\n')
        self._out.write(self.process_inline(line))
    #:

    @override
    def process_inline(self, text: str) -> str:
        import re
        # Negrito: **texto** ou __texto__
        text = re.sub(r'\*\*(.+?)\*\*|__(.+?)__',
                      lambda m: f'<strong>{m.group(1) or m.group(2)}</strong>', text)
        # Itálico: *texto* ou _texto_
        text = re.sub(r'\*(.+?)\*|_(.+?)_',
                      lambda m: f'<em>{m.group(1) or m.group(2)}</em>', text)
        # Imagem: ![alt](url)
        text = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)',
                      lambda m: f'<img src="{m.group(2)}" alt=\'{m.group(1)}\'>', text)
        # Link: [texto](url) ou [texto](url "título") ou [texto]()
        text = re.sub(r'\[([^\]]+)\]\(([^\s\)"]*)?(?:\s+"([^"]*)")?\)',
                  lambda m: (
                      f'<a href="{m.group(2) or ""}" title="{m.group(3)}">{m.group(1)}</a>'
                      if m.group(3) else
                      f'<a href="{m.group(2) or ""}">{m.group(1)}</a>'
                  ), text)
        return text
    #: