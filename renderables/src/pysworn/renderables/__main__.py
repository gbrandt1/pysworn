import logging
from typing import Annotated, TypeAliasType, Union, get_args, get_origin

import typer
from pysworn.common import datasworn_tree
from rich.columns import Columns
from rich.console import Console, RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty
from rich.rule import Rule
from rich.table import Table
from rich.theme import Theme
from rich.tree import Tree

from pysworn.renderables.renderables import RENDERABLE_TYPES, get_renderable

from . import RenderableKeyEnum, RuleSetRenderable

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
def types():
    from inspect import getfullargspec

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

        t = Table("key", "type", "renderable", highlight=True)
        for k, v in keys.items():
            for vv in v:
                renderable = RENDERABLE_TYPES.get(vv, None)
                renderable = f"<{renderable.__name__}>" if renderable else f"[red]None"
                t.add_row(f"'{k}'", f"<{vv.__name__}>", f"{renderable}")
            t.add_section()
        return t

    # print(gather_keys())
    print(get_renderable_table())


@app.command()
def pages(
    render: Annotated[bool, typer.Option("-r", "--render")] = False,
    # filter: Annotated[str, typer.Option("-f", "--filter")] = ".row",
):
    page_index = {}
    for k, v in datasworn_tree.index.items():
        title = None
        page = None
        if source := getattr(v, "source", None):
            # print(source)
            title = source.title
            page = source.page or -1

        if title is None or page is None:
            continue

        d = page_index.setdefault(title, {})
        dd = d.setdefault(page, {})
        dd[k] = v

    for title in sorted(page_index.keys()):
        print(Markdown(f"# {title}"))
        tree = Tree(f"{title}")
        for page in sorted(page_index[title].keys()):
            # print(Rule(f"{page:4}", align="left"))
            node = tree.add(f"{page:4}")
            for k, v in page_index[title][page].items():
                renderable = get_renderable(v)
                print(
                    f"{page:4}",
                    f"{f"'{k}'"}",
                    f"<{type(v).__name__}>",
                    # f"{renderable}",
                )
                # print(Pretty(v))
                if render:
                    print(renderable)
                node.add(k)

        # print(tree)


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
            console.print(Pretty(obj, max_string=40))

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
