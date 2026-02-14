import logging
from encodings.punycode import T
from typing import Annotated, TypeAliasType, Union, get_args, get_origin

import typer
from pysworn.common import datasworn_tree
from pysworn.renderables.renderables import RENDERABLE_TYPES, get_renderable
from rich.columns import Columns
from rich.console import Console, RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty
from rich.rule import Rule
from rich.table import Table
from rich.theme import Theme
from rich.tree import Tree

from . import RenderableKeyEnum, RuleSetRenderable, RulesRenderable

console = Console(force_terminal=True)
console.push_theme(
    Theme(
        {
            "markdown.item.bullet": "white",
            "markdown.item.number": "white",
            "markdown.hr": "white",
            "markdown.link": "italic",
            "markdown.link_url": "italic",
            "markdown.block_quote": "italic",
        }
    )
)

print = console.print

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
logging.getLogger("markdown_it").setLevel(logging.WARNING)

app = typer.Typer(
    # callback=callback,
    no_args_is_help=True,
)


index = datasworn_tree.index


@app.command()
def types(
    keys_: Annotated[bool, typer.Option("--keys", "-k")] = False,
    enum_: Annotated[bool, typer.Option("--enum", "-e")] = False,
    renderables_: Annotated[bool, typer.Option("--renderables", "-r")] = False,
):
    # from inspect import getfullargspec

    from rich.table import Table

    def gather_keys() -> list[str]:
        keys: set[str] = set()
        for k in index:
            if ":" not in k:
                continue
            keys.add(k.split(":")[0])
        print(len(keys))
        return sorted(list(keys))

    def _resolve_type(arg):
        rt: list[str] = []
        if isinstance(arg, TypeAliasType):
            v = get_args(arg.__value__)[0]
        else:
            v = arg

        if get_origin(arg) is Union:
            for arg in get_args(v):
                rt.extend(_resolve_type(arg))
        else:
            rt.append(f"<{v.__name__}>")
        return rt

    def get_renderable_table():
        # for k, v in RENDERABLE_KEYS.items():
        keys: dict[str, set[type]] = {}
        for k, v in index.items():
            # fullargspec = getfullargspec(v.__init__)
            # arg = fullargspec.args[1]
            # annotation = fullargspec.annotations[arg]
            # targets = _resolve_type(annotation)

            key = k.split(":")[0]
            keys.setdefault(key, set())
            keys[key].add(type(v))

        t = Table(
            "key",
            "type",
            "renderable",
            highlight=True,
            show_lines=False,
            show_edge=False,
        )
        for k, v in keys.items():
            for vv in v:
                renderable = RENDERABLE_TYPES.get(vv, None)
                renderable = f"<{renderable.__name__}>" if renderable else f"[red]None"
                t.add_row(f"'{k}'", f"<{vv.__name__}>", f"{renderable}")
            # t.add_section()
        return t

    keys = gather_keys()
    if keys_:
        for k in keys:
            print(k)
    if enum_:
        for k in keys:
            print(f'{k.upper().replace(".", "_")} = "{k}"')

    if renderables_:
        print(get_renderable_table())


@app.command()
def pages(
    render: Annotated[bool, typer.Option("-r", "--render")] = False,
    # filter: Annotated[str, typer.Option("-f", "--filter")] = ".row",
):
    from pysworn.renderables.utils import pages

    renderables = pages(render)
    for r in renderables:
        print(r)


@app.command("print")
def print_(
    prefix: Annotated[
        RenderableKeyEnum,
        typer.Option(
            "--prefix",
        ),
    ] = RenderableKeyEnum.RULESETS,
    debug: Annotated[bool, typer.Option("--debug", "-d")] = False,
    panel: Annotated[bool, typer.Option("--panel", "-p")] = False,
    no_rows: Annotated[bool, typer.Option("--no-rows", "-r")] = False,
    columns: Annotated[bool, typer.Option("--columns", "-c")] = False,
    # id_: Annotated[str, typer.Option("--id", "-i")] = None,
):
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    log.debug(f"prefix: {prefix.value}")

    if prefix.value == "rulesets":
        renderable = RuleSetRenderable
        for ruleset in datasworn_tree:
            print(
                Panel(
                    renderable(datasworn_tree[ruleset]),
                    title=f"[dim]{ruleset} {prefix.value.upper()}",
                    title_align="left",
                    border_style="dim",
                    # width=80,
                )
            )
        return

    if prefix.value == "rules":
        renderable = RulesRenderable
        for ruleset in datasworn_tree:
            print(
                Panel(
                    renderable(datasworn_tree[ruleset].rules),
                    title=f"[dim]{ruleset} {prefix.value.upper()}",
                    title_align="left",
                    border_style="dim",
                    # width=80,
                )
            )
        return

    renderables: list[RenderableType] = []

    for link, v in index.items():
        rule_key = link.split(":")[0]
        if prefix != RenderableKeyEnum.ALL and rule_key != prefix.value:
            continue
        if no_rows and rule_key.endswith(".row"):
            continue
        obj = index[link]

        renderable = get_renderable(obj)
        if columns:
            renderables.append(renderable)
            continue
        if debug:
            print(
                f"[i dim]{link}[/] --> <{type(renderable).__name__}>(<{type(obj).__name__}>)"
            )
        console.print(renderable)
        if debug:
            console.print(Pretty(obj, max_string=80))

    if columns:
        console.print(Columns(renderables))


@app.callback()
def main(
    ruleset: Annotated[list[str], typer.Option("--ruleset", "-r")] = [],
):
    if ruleset == []:
        for k in datasworn_tree:
            datasworn_tree[k]
    else:
        for k in ruleset:
            datasworn_tree[k]
    # datasworn_tree["sundered_isles"]

    t = Table.grid(padding=(0, 1), pad_edge=False)

    for k in datasworn_tree:
        num = sum(1 for i in index.keys() if k in i)
        t.add_row(f"{k}", f"{num}")

    console.print(t)


if __name__ == "__main__":
    app()
