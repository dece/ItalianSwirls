"""Glue between Jedi and LSP data structures."""

import bisect
import difflib
from typing import Generator, Optional, Union

from jedi.api.classes import Name
from jedi.api.refactoring import Refactoring
from pygls.lsp.types import (CompletionItemKind, Location, Position, Range,
                             RenameFile, RenameFileOptions,
                             ResourceOperationKind, TextDocumentEdit, TextEdit,
                             VersionedTextDocumentIdentifier)
from pygls.workspace import Workspace

JEDI_COMPLETION_TYPE_MAP = {
    "module": CompletionItemKind.Module,
    "class": CompletionItemKind.Class,
    "instance": CompletionItemKind.Variable,
    "function": CompletionItemKind.Function,
    "param": CompletionItemKind.Variable,
    "path": CompletionItemKind.File,
    "keyword": CompletionItemKind.Keyword,
    "property": CompletionItemKind.Property,
    "statement": CompletionItemKind.Variable,
}


def get_jedi_position(position: Position) -> tuple[int, int]:
    """Translate LSP Position to Jedi position (where line is 1-based)."""
    return position.line + 1, position.character


def get_lsp_position(line: int, column: int) -> Position:
    """Translate Jedi position to LSP Position (where line is 0-based)."""
    return Position(line=line - 1, character=column)


def get_lsp_range(name: Name) -> Optional[Range]:
    """Get an LSP range for this name, if it has a location."""
    if name.line is None or name.column is None:
        return None
    start_position = get_lsp_position(name.line, name.column)
    end_position = get_lsp_position(name.line, name.column + len(name.name))
    return Range(start=start_position, end=end_position)


def get_lsp_location(name: Name) -> Optional[Location]:
    """Return an LSP location from this Jedi Name."""
    if name.module_path is None:
        return None
    if (lsp_range := get_lsp_range(name)) is None:
        return None
    return Location(uri=name.module_path.as_uri(), range=lsp_range)


def get_lsp_locations(names: list[Name]) -> list[Location]:
    """Return a list of LSP locations from this list of Jedi Names.

    Names that cannot be converted to a LSP location are discarded.
    """
    lsp_locations = []
    for name in names:
        if lsp_location := get_lsp_location(name):
            lsp_locations.append(lsp_location)
    return lsp_locations


def get_lsp_completion_kind(jedi_compl_type: str) -> CompletionItemKind:
    """Return an LSP completion item kind from this Jedi completion type."""
    return JEDI_COMPLETION_TYPE_MAP.get(
        jedi_compl_type,
        CompletionItemKind.Text
    )


def _build_line_offsets(text: str) -> list[int]:
    """Return a list of indexes where each line of the text starts."""
    line_offsets = []
    offset = 0
    for line in text.splitlines(keepends=True):
        line_offsets.append(offset)
        offset += len(line)
    return line_offsets


def _get_lsp_position_from_offsets(
    line_offsets: list[int],
    offset: int,
) -> Position:
    """Return an LSP Position for this offset, using these line offsets."""
    line_number = bisect.bisect_right(line_offsets, offset) - 1
    character_number = offset - line_offsets[line_number]
    return Position(line=line_number, character=character_number)


def gen_document_edits(
    refactoring: Refactoring,
    workspace: Workspace,
) -> Generator[Union[TextDocumentEdit, RenameFile], None, None]:
    """Generate TextDocumentEdit and RenameFile objects from a refactoring."""
    yield from _gen_document_text_edits(refactoring, workspace)
    yield from _gen_document_renames(refactoring, workspace)


def _gen_document_text_edits(
    refactoring: Refactoring,
    workspace: Workspace,
) -> Generator[TextDocumentEdit, None, None]:
    """Generate TextDocumentEdit objects for each text modification.

    Compare previous code and refactored code using standard difflib. The main
    complexity here is to translate difflib's opcode positions into LSP ranges.
    This code is 99% taken from the neat jedi-language-server implementation.
    """
    for path, changed_file in refactoring.get_changed_files().items():
        document_uri = path.as_uri()
        document = workspace.get_document(document_uri)
        old_code = document.source
        new_code = changed_file.get_new_code()
        line_offsets = _build_line_offsets(old_code)
        edit_operations = (
            opcode for opcode in
            difflib.SequenceMatcher(a=old_code, b=new_code).get_opcodes()
            if opcode[0] != "equal"
        )
        text_edits: list[TextEdit] = []
        for op, old_start, old_end, new_start, new_end in edit_operations:
            new_text = new_code[new_start:new_end]
            start_pos = _get_lsp_position_from_offsets(line_offsets, old_start)
            end_pos = _get_lsp_position_from_offsets(line_offsets, old_end)
            edit_range = Range(start=start_pos, end=end_pos)
            text_edits.append(TextEdit(range=edit_range, new_text=new_text))
        if not text_edits:
            continue

        document_id = VersionedTextDocumentIdentifier(
            uri=document_uri,
            version=document.version or 0,
        )
        yield TextDocumentEdit(
            text_document=document_id,
            edits=text_edits,
        )


def _gen_document_renames(
    refactoring: Refactoring,
    workspace: Workspace,
) -> Generator[RenameFile, None, None]:
    """Generate RenameFile objects for each renamed file."""
    for old_name, new_name in refactoring.get_renames():
        yield RenameFile(
            kind=ResourceOperationKind.Rename,
            old_uri=old_name.as_uri(),
            new_uri=new_name.as_uri(),
            options=RenameFileOptions(ignore_if_exists=True, overwrite=True)
        )
