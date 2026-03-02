"""
Markos - Compilador de Markdown Simplificado

Usage:
  markos.py [-s STYLE_SHEET] [-p] [-l] [INPUT_FILE] [OUTPUT_FILE]
  markos.py (-h | --help)

Options:
  -h --help              Mostrar este ecra de ajuda
  -s --style-sheet PATH  Caminho para folha de estilos CSS
  -p --pretty            Output HTML com indentacao (pretty print)
  -l --latex             Gerar output em LaTeX em vez de HTML
  INPUT_FILE             Ficheiro Markdown de entrada (stdin se omitido)
  OUTPUT_FILE            Ficheiro HTML de saida (stdout se omitido)

Examples:
  python markos.py teste.md saida.html
  python markos.py -p -s style.css teste.md saida.html
  python markos.py -l teste.md saida.tex
  python markos.py < input.md > output.html
"""
import sys
from contextlib import closing

from docopt import docopt
from html_backend import HTMLBackend
from markdown_compiler import MarkdownCompiler
from utils import from_file_or_stdin, to_file_or_stdout


def main():
    args = docopt(__doc__)
    style_sheet  = args['--style-sheet']
    pretty_print = args['--pretty']
    use_latex    = args['--latex']   # Acrescentei

    try:
        in_file  = from_file_or_stdin(args['INPUT_FILE'])
        out_file = to_file_or_stdout(args['OUTPUT_FILE'])

        # Acrescentei
        if use_latex:
            from latex_backend import LatexBackend
            backend = LatexBackend(out_file)
        else:
            backend = HTMLBackend(out_file, style_sheet, pretty_print)
        #:

        with in_file, out_file, closing(backend):
            compiler = MarkdownCompiler(backend)
            compiler.compile(in_file)
        #:
    #:

    except FileNotFoundError as ex:
        print(f"File not found: {ex.filename}", file=sys.stderr)
        sys.exit(2)
    #:

    except PermissionError as ex:
        print(f"Invalid permissions to access file: {ex.filename}", file=sys.stderr)
        sys.exit(13)
    #:

    except Exception as ex:
        print(f"An error has occurred:\n {ex.args}\n\n", file=sys.stderr)
        sys.exit(1)
    #:

if __name__ == '__main__':
    main()
