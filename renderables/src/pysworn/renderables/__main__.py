import logging
import re
from typing import Annotated

import typer
from datasworn.core import datasworn_tree, index
from rich import print
from rich.columns import Columns
from rich.console import RenderableType
from rich.panel import Panel

app = typer.Typer()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# trigger lazy loading

# for k in datasworn_tree:
#     print(k)
#     datasworn_tree[k]
# datasworn_tree["classic"]
# datasworn_tree["delve"]
datasworn_tree["starforged"]
# datasworn_tree["starsmith"]
# datasworn_tree["sundered_isles"]
# datasworn_tree["ancient_wonders"]
# datasworn_tree["fe_runners"]


@app.command()
def main(
    prefix: Annotated[str, typer.Option("--prefix")] = "",
    debug: Annotated[bool, typer.Option("--debug", "-d")] = False,
    panel: Annotated[bool, typer.Option("--panel", "-p")] = False,
    no_rows: Annotated[bool, typer.Option("--no-rows", "-r")] = False,
    columns: Annotated[bool, typer.Option("--columns", "-c")] = False,
):
    from pysworn.renderables import RENDERABLES

    # print(index.keys())

    if prefix == "rules":
        renderable = RENDERABLES["rules"]
        for ruleset in rules:
            print(
                Panel(
                    renderable(rules[ruleset].rules),
                    title=f"[dim]{ruleset} {prefix.upper()}",
                    title_align="left",
                    border_style="dim",
                    # width=80,
                )
            )
    renderables: list[RenderableType] = []
    for link, v in index.items():
        if ":" not in link:
            continue
        rule_type = link.split(":")[0]
        if len(prefix) > 0 and rule_type != prefix:
            # print(rule_type)
            continue
        if no_rows and rule_type.endswith(".row"):
            continue
        renderable = RENDERABLES.get(rule_type)
        if debug:
            print(f"[i dim]{link}[/] --> {renderable} {type(index[link]).__name__}")
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
