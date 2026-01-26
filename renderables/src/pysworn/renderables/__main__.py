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

from pysworn.renderables.renderables import get_renderable

from . import RENDERABLE_KEYS, RenderableKeyEnum, RuleSetRenderable

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
app = typer.Typer(
    # callback=callback,
    no_args_is_help=True,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
logging.getLogger("markdown_it").setLevel(logging.WARNING)
# trigger lazy loading

for k in datasworn_tree:
    datasworn_tree[k]

# datasworn_tree["sundered_isles"]

t = Table.grid(padding=(0, 1), pad_edge=False)
index = datasworn_tree.index
for k in datasworn_tree:
    num = sum(1 for i in index.keys() if k in i)
    t.add_row(f"{k}", f"{num}")

console.print(t)


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
        t = Table("key", "renderable", "targets", highlight=True)
        for k, v in RENDERABLE_KEYS.items():
            fullargspec = getfullargspec(v.__init__)
            # if not fullargspec:
            #     print("No renderable defined for {k}  {v.__name__}")
            # print(fullargspec)
            targets = []
            arg = fullargspec.args[1]
            annotation = fullargspec.annotations[arg]
            targets.extend(_resolve_type(annotation))
            t.add_row(f"'{k}'", f"<{v.__name__}>", Columns(targets))
        return t

    print(gather_keys())
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
            page = source.page

        if title is None or page is None:
            continue

        d = page_index.setdefault(title, {})
        dd = d.setdefault(page, {})
        dd[k] = v

    for title in sorted(page_index.keys()):
        print(Markdown(f"# {title}"))
        tree = Tree(f"{title}")
        for page in sorted(page_index[title].keys()):
            print(Rule(f"{page:4}", align="left"))
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

        print(tree)


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
        r_type = RuleSetRenderable
        for ruleset in datasworn_tree:
            print(
                Panel(
                    r_type(datasworn_tree[ruleset]),
                    title=f"[dim]{ruleset} {prefix.value.upper()}",
                    title_align="left",
                    border_style="dim",
                    # width=80,
                )
            )
        return

    renderables: list[RenderableType] = []
    for link, v in index.items():
        if ":" not in link:
            continue
        rule_key = link.split(":")[0]
        if prefix != RenderableKeyEnum.ALL and rule_key != prefix.value:
            # print(rule_type)
            continue
        if no_rows and rule_key.endswith(".row"):
            continue
        log.debug(f"rule_key: {rule_key}")
        r_type = RENDERABLE_KEYS.get(rule_key)
        if debug:
            print(f"[i dim]{link}[/] --> {r_type} {type(index[link]).__name__}")
            # continue
        if r_type:
            renderable: RenderableType = r_type(index[link])
            if panel:
                renderable = get_renderable(index[link])
                # Panel(
                #     renderable,
                #     title=f"[dim]{prefix.value.upper()}",
                #     title_align="left",
                #     border_style="dim",
                #     width=80,
                # )
            else:
                renderable = r_type(index[link])

            console.print(renderable)

    # if columns:
    #     print(
    #         Columns(
    #             renderables,
    #             expand=True,
    #             # equal=True,
    #             # column_first=True,
    #         )
    #     )
    # else:
    #     for renderable in renderables:
    #         print(renderable)


if __name__ == "__main__":
    app()
