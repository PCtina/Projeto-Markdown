"""
Backend para geração de HTML
"""

from abc import ABC, abstractmethod
from typing import TextIO
from io import StringIO
from typing_extensions import override

class MarkdownBackend(ABC):
    @abstractmethod
    def open_document(self, title=''): pass

    @abstractmethod
    def close_document(self): pass

    @abstractmethod
    def open_heading(self, level: int): pass

    @abstractmethod
    def close_heading(self, level: int): pass

    @abstractmethod
    def new_text_line(self, line: str): pass

    @abstractmethod
    def open_par(self): pass      

    @abstractmethod
    def close_par(self): pass     

    @abstractmethod
    def new_par_line(self, line: str): pass

    @abstractmethod
    def open_list(self): pass     

    @abstractmethod
    def close_list(self): pass    

    @abstractmethod
    def open_list_item(self): pass

    @abstractmethod
    def close_list_item(self): pass

    # Acrescentei
    @abstractmethod
    def open_ordered_list(self): pass

    @abstractmethod
    def close_ordered_list(self): pass

    @abstractmethod
    def process_inline(self, text: str) -> str: pass


















class HTMLBackend(MarkdownBackend):
    def __init__(self, out, style_sheet='', pretty_print=False):
        self._storage = out
        self._out = StringIO()
        self._style_sheet = style_sheet
        self._pretty_print = pretty_print
    #:

    def close(self):
        self._storage.write(
            prettify_html( self._out.getvalue())
                if self._pretty_print 
                else self._out.getvalue()
            )
        self._out.close()
    #:

    @override
    def open_document(self, title = ''):
        out = self._out
        out.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

""".replace('\n', ''))
        if title:
            out.write(f'<title>{title}</title>\n')
        if self._style_sheet:
            out.write(f'<link rel="stylesheet" media="all" type="text/css" 'f'src="{self._style_sheet}">\n')
        out.write('\n</head>\n<body>\n')
    #:

    @override
    def close_document(self):
        self._out.write('\n</body>\n</html>\n')