from io import StringIO
import re
from enum import Enum
from typing import TextIO
from functools import singledispatchmethod

from markdown_backend import MarkdownBackend
from markdown_list import (
    MarkdownList,
    ListItem,
    ListItemInnerElem,
    ListItemBlock,
    ListItemSubList, # Acrescentei
    ListItemHeading,
)
from utils import count_consec, matches, rewind_one_line

__all__ = [
    'MarkdownCompiler',
    'CompilationError',
]


class CompilationError(Exception):
    """A generic compilation error."""


class MarkdownCompiler:
    """Simplified Markdown parser and compiler."""

    INLINE_TITLE_MARKER   = '!'
    INLINE_HEADING_MARKER = '#'
    INLINE_ULIST_MARKER   = '-'
    INLINE_ULIST_MARKER2  = '*'   # Acrescentei : suporte a '*' como marcador

    BLANK_LINE            = re.compile(r'[ \t\n\r]*')
    UNINDENT_HEADING_LINE = re.compile(r'\s?#{1,6}(\s+.*)?')
    INDENT_HEADING_LINE   = re.compile(r'\s{2,}(#{1,6})(?:\s+.*)?$')
    UNINDENT_TEXT_LINE    = re.compile(r'\s?\S.*')
    INDENT_TEXT_LINE      = re.compile(r'\s{2,}\S.*')
    # LIST_ITEM_LINE      = re.compile(r'\s{,3}-(\s+.*)?')
    LIST_ITEM_LINE        = re.compile(r'\s{,3}[-*](\s+.*)?')  # Acrescentei : aceita '-' e '*'
    OLIST_ITEM_LINE       = re.compile(r'\s{,3}\d+[.)]\s*\S.*')  # Acrescentei : aceita 1. e  1)
    TITLE_LINE            = re.compile(r'!.*\S.*!')

    def __init__(self, backend: MarkdownBackend):
        self._backend = backend
    #:

    def compile(self, in_: TextIO | str):
        if isinstance(in_, str):
            in_ = StringIO(in_)

        backend = self._backend
        title = self._read_title(in_)
        backend.open_document(title)

        CompilerState = Enum('CompilerState', 'OUTSIDE INSIDE_PAR NEW_LIST')
        state = CompilerState.OUTSIDE

        while True:
            pos = in_.tell()
            line = in_.readline()
            if not line:
                break
            line = line.rstrip('\r\n')

            if state is CompilerState.OUTSIDE and self._is_heading_line(line):
                self._new_heading(line)

            elif state is CompilerState.OUTSIDE and matches(self.LIST_ITEM_LINE, line):
                rewind_one_line(in_, pos)
                self._compile_list(in_)
                state = CompilerState.NEW_LIST
            #:

            # Acrescentei : deteção de listas ordenadas
            elif state is CompilerState.OUTSIDE and matches(self.OLIST_ITEM_LINE, line):
                rewind_one_line(in_, pos)
                self._compile_list(in_, ordered=True)
                state = CompilerState.NEW_LIST
            #:

            elif state is CompilerState.OUTSIDE and self._is_text_line(line):
                backend.open_par()
                backend.new_par_line(line)
                state = CompilerState.INSIDE_PAR
            #:

            elif state is CompilerState.OUTSIDE and matches(self.BLANK_LINE, line):
                pass  # linha em branco fora de parágrafo: ignorar
            #:

            elif state is CompilerState.INSIDE_PAR and self._is_heading_line(line):
                backend.close_par()
                self._new_heading(line)
                state = CompilerState.OUTSIDE
            #:

            elif state is CompilerState.INSIDE_PAR and matches(self.BLANK_LINE, line):
                backend.close_par()
                state = CompilerState.OUTSIDE
            #:

            elif state is CompilerState.INSIDE_PAR and matches(self.LIST_ITEM_LINE, line):
                backend.close_par()
                rewind_one_line(in_, pos)
                self._compile_list(in_)
                state = CompilerState.NEW_LIST
            #:

            # Acrescentei : deteção de listas ordenadas
            elif state is CompilerState.INSIDE_PAR and matches(self.OLIST_ITEM_LINE, line):
                backend.close_par()
                rewind_one_line(in_, pos)
                self._compile_list(in_, ordered=True)
                state = CompilerState.NEW_LIST
            #:

            elif state is CompilerState.INSIDE_PAR and self._is_text_line(line):
                backend.new_par_line(line)
            #:

            elif state is CompilerState.NEW_LIST and self._is_heading_line(line):
                self._new_heading(line)
                state = CompilerState.OUTSIDE
            #:

            elif state is CompilerState.NEW_LIST and self._is_text_line(line):
                backend.open_par()
                backend.new_par_line(line)
                state = CompilerState.INSIDE_PAR
            #:

            else:
                assert matches(self.BLANK_LINE, line), \
                    f'Unknown line \"{line}\" for state {state}'
            #:

        backend.close_document()
    #:

    def _new_heading(self, line_with_markers: str):
        backend = self._backend
        text, level = self._parse_heading(line_with_markers)
        backend.open_heading(level)
        backend.new_text_line(text)
        backend.close_heading(level)
    #:

    def _parse_heading(self, line_with_markers: str) -> tuple[str, int]:
        line_with_markers = line_with_markers.lstrip()
        count = count_consec(line_with_markers, self.INLINE_HEADING_MARKER)
        assert count > 0, 'No heading markers found'
        text = line_with_markers[count:].strip()
        return text, count
    #:

    def _is_heading_line(self, line: str) -> bool:
        return (
            matches(self.UNINDENT_HEADING_LINE, line)
            or matches(self.INDENT_HEADING_LINE, line)
        )

    def _is_text_line(self, line: str) -> bool:
        return (
            matches(self.UNINDENT_TEXT_LINE, line)
            or matches(self.INDENT_TEXT_LINE, line)
        )
    #:

    def _read_title(self, in_: TextIO) -> str:
        first_line  = in_.readline().rstrip('\r\n')
        second_line = in_.readline()
        if matches(self.TITLE_LINE, first_line) and matches(self.BLANK_LINE, second_line):
            return first_line[1:-1].strip()
        in_.seek(0)
        return ''
    #:

    # Acrescentei : suporte para listas ordenadas
    def _compile_list(self, in_: TextIO, ordered: bool = False):
        pos = in_.tell()
        line = in_.readline().rstrip('\r\n')

        # Seleciona o padrão correto conforme o tipo de lista
        item_pattern = self.OLIST_ITEM_LINE if ordered else self.LIST_ITEM_LINE

        assert matches(item_pattern, line), \
            f'First line not a list item line: |{line}|'

        mkd_list = MarkdownList()
        mkd_list.ordered = ordered   # <- NOVO atributo no MarkdownList (ver abaixo)
        curr_list_item = mkd_list.add_new_list_item(
            self._new_list_item_inner_elem(line, ordered)
        )

        ListState = Enum('ListState', 'LIST_ITEM MAY_END')
        state = ListState.LIST_ITEM

        while True:
            pos = in_.tell()
            line = in_.readline()
            if not line:
                break
            line = line.rstrip('\r\n')

            if matches(self.UNINDENT_HEADING_LINE, line):
                rewind_one_line(in_, pos)
                break
            #:

            elif state is ListState.LIST_ITEM and matches(item_pattern, line):
                curr_list_item = mkd_list.add_new_list_item(
                    self._new_list_item_inner_elem(line, ordered)
                )
            #:

            elif state is ListState.LIST_ITEM and matches(self.INDENT_HEADING_LINE, line):
                curr_list_item.append(self._new_list_item_heading(line))
            #:

            # NOVO: sub-lista indentada (  - sub item)
            elif state is ListState.LIST_ITEM and matches(re.compile(r'\s{2,}[-*]\s+.*'), line):
                sub_mkd = MarkdownList()
                sub_mkd.ordered = False
                sub_item_text = re.sub(r'^\s+[-*]\s+', '', line)
                sub_mkd.add_new_list_item(ListItemBlock(sub_item_text))
                from markdown_list import ListItemSubList
                curr_list_item.append(ListItemSubList(sub_mkd))
            #:

            elif state is ListState.LIST_ITEM and matches(self.INDENT_TEXT_LINE, line):
                curr_list_item.append(ListItemBlock(line.strip()))
                mkd_list.with_paragraphs = True
            #:

            elif state is ListState.LIST_ITEM and matches(self.BLANK_LINE, line):
                state = ListState.MAY_END
            #:

            elif state is ListState.MAY_END and matches(item_pattern, line):
                curr_list_item = mkd_list.add_new_list_item(
                    self._new_list_item_inner_elem(line, ordered)
                )
                mkd_list.with_paragraphs = True
                state = ListState.LIST_ITEM
            #:

            elif state is ListState.MAY_END and matches(self.INDENT_HEADING_LINE, line):
                curr_list_item.append(self._new_list_item_heading(line))
                mkd_list.with_paragraphs = True
                state = ListState.LIST_ITEM
            #:

            elif state is ListState.MAY_END and matches(self.INDENT_TEXT_LINE, line):
                # Texto indentado após linha em branco = novo parágrafo dentro do item actual
                curr_list_item.append(ListItemBlock(line.strip()))
                mkd_list.with_paragraphs = True
                state = ListState.LIST_ITEM
            #:

            elif state is ListState.MAY_END and matches(self.UNINDENT_TEXT_LINE, line):
                rewind_one_line(in_, pos)
                break   
            #:

            elif state is ListState.LIST_ITEM and matches(self.UNINDENT_TEXT_LINE, line):
                rewind_one_line(in_, pos)
                break
            #:

            else:
                assert state is ListState.MAY_END and matches(self.BLANK_LINE, line), \
                    f'Unknown line "{line}" for state {state}'
            #:

        self._compile_markdown_list(mkd_list)
    #:

    # def _new_list_item_inner_elem(self, initial_line: str) -> ListItemInnerElem:
    #     line = initial_line.strip()[1:].strip()
    #     if self._is_heading_line(line):
    #         return self._new_list_item_heading(line)
    #     return ListItemBlock(line)
    #:

    # Acrescentei : suporte * 1. 1)
    def _new_list_item_inner_elem(self, initial_line: str, ordered: bool = False) -> ListItemInnerElem:
        line = initial_line.strip()
        if ordered:
            # Remove  "1. " ou "1) "
            line = re.sub(r'^\d+[.)]\s*', '', line)
        else:
            # Remove "- " ou "* "
            line = re.sub(r'^[-*]\s+', '', line)
        if self._is_heading_line(line):
            return self._new_list_item_heading(line)
        return ListItemBlock(line)
    #:


    def _new_list_item_heading(self, line_with_markers: str) -> ListItemHeading:
        line, level = self._parse_heading(line_with_markers)
        return ListItemHeading(line, level)
    #:

    # def _compile_markdown_list(self, mkd_list: MarkdownList):
    #     backend = self._backend
    #     backend.open_list()
    #     for list_item in mkd_list:
    #         self._compile_list_item(list_item, mkd_list.with_paragraphs)
    #     backend.close_list()
    #:

    # Acrescentei 
    def _compile_markdown_list(self, mkd_list: MarkdownList):
        backend = self._backend
        if getattr(mkd_list, 'ordered', False):
            backend.open_ordered_list()
        else:
            backend.open_list()

        for list_item in mkd_list:
            self._compile_list_item(list_item, mkd_list.with_paragraphs)

        if getattr(mkd_list, 'ordered', False):
            backend.close_ordered_list()
        else:
            backend.close_list()
    #:

    def _compile_list_item(self, list_item: ListItem, with_paragraphs: bool):
        backend = self._backend
        backend.open_list_item()
        for inner_elem in list_item:
            self._compile_list_item_inner_elem(inner_elem, with_paragraphs)
        backend.close_list_item()
    #:

    @singledispatchmethod
    def _compile_list_item_inner_elem(self, elem, *_, **__):
        raise NotImplementedError(f"Unknown inner elem '{elem}' of type {type(elem)}")

    @_compile_list_item_inner_elem.register
    def _(self, block: ListItemBlock, with_paragraphs: bool = False):
        backend = self._backend
        if with_paragraphs:
            backend.open_par()
            backend.new_par_line(str(block))
            backend.close_par()
        else:
            backend.new_par_line(str(block))
    #:

    @_compile_list_item_inner_elem.register
    def _(self, heading: ListItemHeading, *_):
        backend = self._backend
        backend.open_heading(heading.level)
        backend.new_text_line(str(heading))
        backend.close_heading(heading.level)
    #:

    # Acrescentei
    @_compile_list_item_inner_elem.register
    def _(self, sub: ListItemSubList, *_):
        # Gera sub-lista <ul>...</ul> dentro do <li> atual
        self._compile_markdown_list(sub.inner_list)
    #:
#:
