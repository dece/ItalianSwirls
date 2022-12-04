import logging
from typing import Optional

from jedi import Script
from jedi.api.refactoring import RefactoringError
from pygls.lsp.methods import (COMPLETION, DEFINITION, HOVER, REFERENCES,
                               RENAME, TYPE_DEFINITION)
from pygls.lsp.types import (CompletionItem, CompletionList, CompletionOptions,
                             CompletionParams, DefinitionParams, Hover,
                             HoverParams, InsertTextFormat, Location,
                             ReferenceParams, RenameParams,
                             TextDocumentPositionParams, TypeDefinitionParams,
                             WorkspaceEdit)
from pygls.server import LanguageServer
from pygls.workspace import Document

from italianswirls.glue import (gen_document_edits, get_jedi_position,
                                get_lsp_completion_kind, get_lsp_locations)

LS = LanguageServer('italianswirls', 'v0.0.1')


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


@LS.feature(REFERENCES)
async def do_references(
    server: LanguageServer,
    params: ReferenceParams,
) -> Optional[list[Location]]:
    """Return the type definition location(s) of the target symbol."""
    script = get_jedi_script_from_params(params, server)
    jedi_position = get_jedi_position(params.position)
    jedi_names = script.get_references(*jedi_position)
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


@LS.feature(RENAME)
async def do_rename(
    server: LanguageServer,
    params: RenameParams,
) -> Optional[WorkspaceEdit]:
    """Ask Jedi to rename a symbol and return the resulting state."""
    script = get_jedi_script_from_params(params, server)
    jedi_position = get_jedi_position(params.position)
    try:
        refactoring = script.rename(*jedi_position, new_name=params.new_name)
    except RefactoringError as exc:
        logging.error(f"Refactoring failed: {exc}")
        return None

    changes = list(gen_document_edits(refactoring, server.workspace))
    logging.info(f"changes: {changes}")
    return WorkspaceEdit(document_changes=changes) if changes else None
