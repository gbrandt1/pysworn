from dataclasses import fields, is_dataclass
from inspect import cleandoc, getdoc, isclass
from typing import Any, Iterable, Optional

from rich import print
from rich._inspect import Inspect as RichInspect
from rich.console import Group, RenderableType
from rich.control import escape_control_codes
from rich.highlighter import ReprHighlighter
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text, TextType

# Datasworn metadata attributes
DATASWORN_META = [
    # "authors",
    # "color",
    # "type",
    # "name",
    # "title",
    # "id",
    # "icon",
    # "source",
    # "url",
    "i18n",
    # "template",
    # "date",
    # "oracle_type",
    # "text",
]


class Inspect:
    """A Renderable to inspect Datasworn classes.

    This is a modified version of the original Rich Inspect renderable.
    It does not contain any specific Datasworn classes or attributes (apart from the metadata list).

    Args:
        obj (Any): Object to inspect.
        title (str, optional): Title to display over inspect result, or None use type. Defaults to None.
        docs (bool, optional): Also render doc strings. Defaults to False.
        empty (bool, optional): Print objects with None or falsy value. Defaults to False.
        meta (bool, optional): Print objects in metadata list. Defaults to False.
        max_depth (int, optional): Pass to Pretty
        max_string (int, optional): Pass to Pretty
        max_length (int, optional): Pass to Pretty
    """

    def __init__(
        self,
        obj: Any,
        *,
        title: Optional[TextType] = None,
        docs: bool = False,
        empty: bool = False,
        meta: bool = False,
        max_depth: int = 1000,
        max_string: int | None = None,
        max_length: int | None = None,
    ) -> None:
        self.highlighter = ReprHighlighter()
        self.obj = obj
        self.title = title or self._make_title(obj)
        self.docs = docs  # or help
        self.empty = empty
        self.meta = meta
        self.max_depth = max_depth
        self.max_string = max_string
        self.max_length = max_length

    def _make_title(self, obj: Any) -> Text:
        """Make a default title."""
        title_str = str(obj) if isclass(obj) else str(type(obj))
        title_text = self.highlighter(title_str)
        return title_text

    def __rich__(self) -> Panel:
        return Panel.fit(
            Group(*self._render()),
            title=self.title,
            border_style="scope.border",
            padding=(0, 1),
        )

    def _render(self) -> Iterable[RenderableType]:
        """Render object."""

        if self.max_depth == 0:
            return

        obj = self.obj

        # fallback to Rich inspect
        if not is_dataclass(obj):
            yield RichInspect(
                obj,
                sort=True,
                all=False,
                value=True,
                docs=True,
            )
            return

        # keys = dir(obj)
        keys = [field.name for field in fields(obj)]

        if not self.empty:
            ignored_empty = [key for key in keys if not getattr(obj, key)]
            keys = [key for key in keys if getattr(obj, key)]

        if not self.meta:
            ignored_meta = [key for key in keys if key in DATASWORN_META]
            keys = [key for key in keys if key not in DATASWORN_META]

        items = [(key, getattr(obj, key)) for key in keys]

        items_table = Table.grid(padding=(0, 1), expand=False)
        items_table.add_column(justify="right")
        add_row = items_table.add_row
        highlighter = self.highlighter

        if self.docs:
            _doc = self._get_formatted_doc(obj)
            if _doc is not None:
                doc_text = Text(_doc, style="inspect.help")
                doc_text = highlighter(doc_text)
                yield doc_text
                yield ""

        for key, value in items:
            key_text = Text.assemble(
                (
                    key,
                    "inspect.attr",
                ),
                (" =", "inspect.equals"),
            )

            rendered_value: RenderableType
            if is_dataclass(value) and len(fields(value)) > 1:
                #     rendered_value = highlighter(f"{value!r}")
                # else:
                rendered_value = Inspect(
                    value,
                    max_depth=max(0, self.max_depth - 1),
                )
            elif isinstance(value, dict):
                dict_table = Table.grid(padding=(0, 1), expand=False)
                for k, v in value.items():
                    dict_table.add_row(
                        highlighter(f"'{k}' : "),
                        Inspect(
                            v,
                            max_depth=max(0, self.max_depth - 1),
                            # max_depth=self.max_depth,
                            max_length=self.max_length,
                            max_string=self.max_string,
                        ),
                    )
                rendered_value = Group("{", dict_table, "}")
            elif isinstance(value, list):
                l_ = []
                for v in value:
                    l_.append(
                        Inspect(
                            v,
                            max_depth=max(0, self.max_depth - 1),
                            # max_depth=self.max_depth,
                            max_length=self.max_length,
                            max_string=self.max_string,
                        )
                    )
                rendered_value = Group("[", *l_, "]")
            else:
                rendered_value = Pretty(
                    value,
                    highlighter=highlighter,
                    max_depth=self.max_depth,
                    max_length=self.max_length,
                    max_string=self.max_string,
                )
            add_row(
                key_text,
                rendered_value,
            )

        if items_table.row_count:
            yield items_table

        if not self.meta and len(ignored_meta):
            yield Text.assemble(
                ("metadata: ", "dim"),
                (", ".join(ignored_meta), "inspect.attr.dunder"),
            )
        if not self.empty and len(ignored_empty):
            yield Text.assemble(
                ("empty: ", "dim"),
                (", ".join(ignored_empty), "inspect.attr.dunder"),
            )

    def _get_formatted_doc(self, object_: Any) -> Optional[str]:
        """
        Extract the docstring of an object, process it and returns it.
        The processing consists in cleaning up the doctring's indentation,
        taking only its 1st paragraph if `self.help` is not True,
        and escape its control codes.

        Args:
            object_ (Any): the object to get the docstring from.

        Returns:
            Optional[str]: the processed docstring, or None if no docstring was found.
        """
        docs = getdoc(object_)
        if docs is None:
            return None
        docs = cleandoc(docs).strip()
        return escape_control_codes(docs)


def inspect(
    obj: Any,
    *,
    title: Optional[str] = None,
    docs: bool = True,
    empty: bool = False,
    meta: bool = False,
    max_depth: Optional[int] = None,
    max_string: Optional[int] = None,
    max_length: Optional[int] = None,
) -> None:
    """Inspect Datasworn object."""

    _inspect = Inspect(
        obj,
        title=title,
        docs=docs,
        empty=empty,
        meta=meta,
        max_depth=max_depth,
        max_string=max_string,
        max_length=max_length,
    )
    print(_inspect)
