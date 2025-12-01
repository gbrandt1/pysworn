from typing import Annotated

import typer
from pysworn.datasworn import index, rules
from rich import print
from rich.panel import Panel

app = typer.Typer()


@app.command()
def main(
    prefix: Annotated[str, typer.Option("--prefix", "-p")] = "oracle_rollable",
    debug: Annotated[bool, typer.Option("--debug", "-d")] = False,
):
    from pysworn.renderables import RENDERABLES

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

    for link, v in index.items():
        if prefix and not link.startswith(prefix):
            continue
        rule_type = link
        if ":" in link:
            rule_type = link.split(":")[0]
        renderable = RENDERABLES.get(rule_type)
        if debug:
            print(f"[i dim]{link}[/] --> {renderable} {type(index[link]).__name__}")
        if renderable:
            print(
                # Panel(
                renderable(index[link]),
                # title=f"[dim]{prefix.upper()}",
                # title_align="left",
                # border_style="dim",
                # width=80,
                # )
            )
            # print(renderable(index[link]))


if __name__ == "__main__":
    app()
