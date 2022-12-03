import logging

from jedi import Script
from pygls.lsp.methods import COMPLETION, HOVER, INITIALIZE
from pygls.lsp.types import (CompletionItem, CompletionItemKind,
                             CompletionList, CompletionOptions,
                             CompletionParams, Hover, InsertTextFormat,
                             Position, TextDocumentPositionParams)
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
    """Get Jedi Script object from this document and project."""
    return Script(code=document.source, path=document.path)


def get_jedi_position(position: Position) -> tuple[int, int]:
    """Translate pygls's Position to Jedi position (line is 1-based)."""
    return position.line + 1, position.character


def get_pygls_compl_kind(jedi_compl_type: str) -> CompletionItemKind:
    return JEDI_COMPLETION_TYPE_MAP.get(
        jedi_compl_type,
        CompletionItemKind.Text
    )


@LS.feature(INITIALIZE)
async def do_initialize(*args):
    LOG.debug("do_initialize 👋")


@LS.feature(COMPLETION, CompletionOptions(trigger_characters=["."]))
async def do_completion(
    server: LanguageServer,
    params: CompletionParams,
) -> CompletionList:
    """Return completion items."""
    document_uri = params.text_document.uri
    document = server.workspace.get_document(document_uri)
    script = get_jedi_script(document)
    jedi_position = get_jedi_position(params.position)
    jedi_completions = script.complete(*jedi_position)

    completion_items = []
    for jedi_completion in jedi_completions:
        name = jedi_completion.name
        item = CompletionItem(
            label=name,
            filter_text=name,
            kind=get_pygls_compl_kind(jedi_completion.type),
            sort_text=name,
            insert_text_name=name,
            insert_text_format=InsertTextFormat.PlainText,
        )
        completion_items.append(item)

    return CompletionList(
        is_incomplete=False,
        items=completion_items,
    )


@LS.feature(HOVER)
async def do_hover(
    server: LanguageServer,
    params: TextDocumentPositionParams,
) -> Hover:
    """Provide "hover", which is documentation of a symbol.

    Jedi provides a list of names with information, usually only one. We handle
    them all and concatenate them, separated by a horizontal line. For
    simplicity, the text is mostly provided untouched.
    """
    document_uri = params.text_document.uri
    document = server.workspace.get_document(document_uri)
    script = get_jedi_script(document)
    jedi_position = get_jedi_position(params.position)
    jedi_help_names = script.help(*jedi_position)

    help_texts = []
    for jedi_name in jedi_help_names:
        text = f"`{jedi_name.full_name}`"
        if sigs := jedi_name.get_signatures():
            text += "\n" + "\n".join(f"`{sig.to_string()}`" for sig in sigs)
        if docstring := jedi_name.docstring(raw=True):
            text += "\n\n" + docstring
        help_texts.append(text)

    hover_text = "\n\n---\n\n".join(help_texts)
    return Hover(contents=hover_text)  # TODO range


if __name__ == "__main__":
    LS.start_io()
