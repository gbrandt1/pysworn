import logging
from collections import Counter, defaultdict

# from io import StringIO
from typing import Annotated

import typer
from pysworn.reference import rules
from rich import print
from rich.console import Console
from rich.logging import RichHandler
from rich.rule import Rule
from rich.table import Table
from rich.traceback import install

from ._inspect import Inspect
from .main import RULESETS, ParsedId, breadcrumbs, index

install()

console = Console()
# console = Console(file=StringIO(), force_terminal=True)


FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=True)


@app.command()
def count(
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Count IDs by prefix."""
    counts = []
    counts_by_ruleset = defaultdict(list)

    for k, v in index.items():
        if verbose:
            print(k, type(v))
            print(Inspect(v, max_depth=1, max_length=1, max_string=100))
        sk = k.split(":")
        counts.append(sk[0])

        if len(sk) < 2:
            ruleset = sk[0]
        else:
            ruleset = sk[1].split("/")[0]
        counts_by_ruleset[ruleset].append(sk[0])

    table = Table("ID Prefix", "Total", *RULESETS)
    for t in Counter(counts).most_common():
        k = t[0]
        v = t[1]
        table.add_row(
            k,
            repr(v),
            *[repr(counts_by_ruleset[ruleset].count(k)) for ruleset in RULESETS],
        )
    print(table)


@app.command()
def types():
    rule_types = get_rule_types()
    # pprint(rule_types, expand_all=True)
    for r in sorted(rule_types):
        print(r)


@app.command()
def ids(
    skip_rows: Annotated[bool, typer.Option("--skip-rows", "-r")] = False,
    parents: Annotated[bool, typer.Option("--parents", "-p")] = False,
    tree: Annotated[bool, typer.Option("--tree", "-t")] = False,
):
    if tree:
        print(id_tree)
        return

    for k in index.keys():
        if skip_rows and ".row:" in k:
            continue
        # if not parents:
        #     print(k)
        # else:
        #     print(f"{k} --> {get_parent_id(k)}")

        print(f"{ParsedId(k)}")


@app.command()
def names():
    # from collections import Counter

    seen = set()
    for k in index.keys():
        b = breadcrumbs(k)
        if b:
            # b.insert(0, (k.split(":")[1]).split("/")[0])
            strb = " > ".join(b)
            # print(strb)
            # else:
            #     print(f"[i dim]{k}")
            # if strb in seen:
            print(f"[i dim]{k}[/] --> {strb}")
            seen.add(strb)
    # counts = Counter(seen)
    # print(counts.most_common())


@app.command()
def dump():
    for ruleset in rules:
        print(Rule(ruleset))
        for category in vars(rules[ruleset]):
            print(f"  {category}")
            p = Inspect(
                getattr(rules[ruleset], category),
                max_depth=1,
                max_length=None,
                max_string=None,
            )
            console.print(p)


@app.command("rules")
def rules_():
    for ruleset in rules:
        print(Rule(ruleset))
        print(rules[ruleset].rules)


if __name__ == "__main__":
    app()
