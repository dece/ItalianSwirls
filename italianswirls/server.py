import logging
from typing import Optional

from jedi import Script
from jedi.api.classes import Name
from pygls.lsp.methods import COMPLETION, DEFINITION, HOVER, TYPE_DEFINITION
from pygls.lsp.types import (CompletionItem, CompletionItemKind,
                             CompletionList, CompletionOptions,
                             CompletionParams, DefinitionParams, Hover,
                             HoverParams, InsertTextFormat,
                             Location, Position, Range,
                             TextDocumentPositionParams, TypeDefinitionParams)
from pygls.server import LanguageServer
from pygls.workspace import Document

LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.FileHandler("/tmp/a.log"))

LS = LanguageServer('italianswirls', 'v0.0.1')

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


def get_jedi_script(document: Document) -> Script:
    """Get Jedi Script object from this document."""
    return Script(code=document.source, path=document.path)


def get_jedi_script_from_params(
    params: TextDocumentPositionParams,
    server: LanguageServer
) -> Script:
    """Get Jedi Script using text document params provided by the client."""
    document_uri = params.text_document.uri
    document = server.workspace.get_document(document_uri)
    script = get_jedi_script(document)
    return script


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


@LS.feature(COMPLETION, CompletionOptions(trigger_characters=["."]))
async def do_completion(
    server: LanguageServer,
    params: CompletionParams,
) -> CompletionList:
    """Return completion items."""
    script = get_jedi_script_from_params(params, server)
    jedi_position = get_jedi_position(params.position)
    jedi_completions = script.complete(*jedi_position)

    completion_items = []
    for jedi_completion in jedi_completions:
        name = jedi_completion.name
        item = CompletionItem(
            label=name,
            filter_text=name,
            kind=get_lsp_completion_kind(jedi_completion.type),
            sort_text=name,
            insert_text_name=name,
            insert_text_format=InsertTextFormat.PlainText,
        )
        completion_items.append(item)

    return CompletionList(
        is_incomplete=False,
        items=completion_items,
    )


@LS.feature(DEFINITION)
async def do_definition(
    server: LanguageServer,
    params: DefinitionParams,
) -> Optional[list[Location]]:
    """Return the definition location(s) of the target symbol."""
    script = get_jedi_script_from_params(params, server)
    jedi_position = get_jedi_position(params.position)
    jedi_names = script.goto(
        *jedi_position,
        follow_imports=True,
        follow_builtin_imports=True,
    )
    return get_lsp_locations(jedi_names) or None


@LS.feature(TYPE_DEFINITION)
async def do_type_definition(
    server: LanguageServer,
    params: TypeDefinitionParams,
) -> Optional[list[Location]]:
    """Return the type definition location(s) of the target symbol."""
    script = get_jedi_script_from_params(params, server)
    jedi_position = get_jedi_position(params.position)
    jedi_names = script.infer(*jedi_position)
    return get_lsp_locations(jedi_names) or None


@LS.feature(HOVER)
async def do_hover(
    server: LanguageServer,
    params: HoverParams,
) -> Optional[Hover]:
    """Provide "hover", which is the documentation of the target symbol.

    Jedi provides a list of names with information, usually only one. We handle
    them all and concatenate them, separated by a horizontal line. For
    simplicity, the text is mostly provided untouched, including docstrings, so
    if your client tries to interpret it as Markdown even though there are
    rogue `**kwargs` hanging around you might have a few display issues.
    """
    script = get_jedi_script_from_params(params, server)
    jedi_position = get_jedi_position(params.position)
    jedi_help_names = script.help(*jedi_position)
    if not jedi_help_names:
        return None

    help_texts = []
    for jedi_name in jedi_help_names:
        text = ""
        if full_name := jedi_name.full_name:
            text += f"`{full_name}`\n"
        if sigs := jedi_name.get_signatures():
            text += "\n".join(f"`{sig.to_string()}`" for sig in sigs) + "\n"
        if docstring := jedi_name.docstring(raw=True):
            text += "\n" + docstring
        if text:
            help_texts.append(text)
    if not help_texts:
        return None

    hover_text = "\n\n---\n\n".join(help_texts)
    return Hover(contents=hover_text)


if __name__ == "__main__":
    LS.start_io()
