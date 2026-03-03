import sys
import re
from typing import TextIO

from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter

__all__ = [
    'prettify_html',
    'from_file_or_stdin',
    'to_file_or_stdout',
    'matches',
    'count_consec',
    'rewind_one_line',
]


def prettify_html(html_code: str, indent=2) -> str:
    soup = BeautifulSoup(html_code, features='html.parser')
    return soup.prettify(formatter=HTMLFormatter(indent=indent))
#:

# Acrescentei
def rewind_one_line(in_: TextIO, pos_or_line: int | str) -> None:
    if isinstance(pos_or_line, int):
        in_.seek(pos_or_line)
    else:
        # calcula bytes da linha em UTF-8
        line_ending = 2 if in_.newlines == '\r\n' else 1
        n_bytes = len(pos_or_line.encode('utf-8')) + line_ending
        in_.seek(in_.tell() - n_bytes, 0)
#:


def from_file_or_stdin(file_path: str | None) -> TextIO:
    return open(file_path, 'rt', encoding='utf-8') if file_path else sys.stdin
#:

def to_file_or_stdout(file_path: str | None) -> TextIO:
    return open(file_path, 'wt', encoding='utf-8') if file_path else sys.stdout
#:

def matches(pattern: re.Pattern, line: str) -> bool:
    return bool(pattern.fullmatch(line))
#:

def count_consec(txt: str, char: str, start_pos: int = 0) -> int:
    count = 0
    for ch in txt[start_pos:]:
        if ch != char:
            break
        count += 1
    return count
#:

