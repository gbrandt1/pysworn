import logging
from calendar import c
from typing import Annotated

import typer
from datasworn.core import datasworn_tree
from rich import print
from rich.columns import Columns
from rich.console import RenderableType
from rich.panel import Panel

from . import RENDERABLE_KEYS, RenderableKeyEnum, RuleSetRenderable

app = typer.Typer(
    # callback=callback,
    no_args_is_help=True,
)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
logging.getLogger("markdown_it").setLevel(logging.WARNING)
# trigger lazy loading

for k in datasworn_tree:
    print(k)
    datasworn_tree[k]
# datasworn_tree["classic"]
# datasworn_tree["delve"]
# datasworn_tree["starforged"]
# datasworn_tree["starsmith"]
# datasworn_tree["sundered_isles"]
# datasworn_tree["ancient_wonders"]
# datasworn_tree["fe_runners"]

index = datasworn_tree.index


@app.command()
def types():
    from inspect import getfullargspec

    from rich.table import Table

    t = Table.grid(padding=(0, 1), pad_edge=False)
    for k, v in RENDERABLE_KEYS.items():
        fullargspec = getfullargspec(v.__init__).annotations.values()
        if fullargspec:
            target = list(fullargspec)[0]
        else:
            target = None
        t.add_row(k, f"{v.__name__}", f"{target}")

    print(t)


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
        if ":" not in link:
            continue
        rule_key = link.split(":")[0]
        if prefix != RenderableKeyEnum.ALL and rule_key != prefix.value:
            # print(rule_type)
            continue
        if no_rows and rule_key.endswith(".row"):
            continue
        log.debug(f"rule_key: {rule_key}")
        renderable = RENDERABLE_KEYS.get(rule_key)
        if debug:
            print(f"[i dim]{link}[/] --> {renderable} {type(index[link]).__name__}")
            # continue
        if renderable:
            if panel:
                renderables.append(
                    Panel(
                        renderable(index[link]),
                        title=f"[dim]{prefix.upper()}",
                        title_align="left",
                        border_style="dim",
                        width=80,
                    )
                )

            else:
                renderables.append(renderable(index[link]))
    if columns:
        print(
            Columns(
                renderables,
                expand=True,
                # equal=True,
                # column_first=True,
            )
        )
    else:
        for renderable in renderables:
            print(renderable)


if __name__ == "__main__":
    app()
