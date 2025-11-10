import logging
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import fields, is_dataclass
from datetime import datetime

# from io import StringIO
from pathlib import Path
from typing import Annotated, Any

import orjson as json
import pysworn.datasworn._datasworn as _datasworn
import typer
from rich import print
from rich.console import Console
from rich.logging import RichHandler
from rich.rule import Rule
from rich.table import Table
from rich.traceback import install

from ._datasworn import *  # noqa
from ._inspect import Inspect

install()

console = Console()
# console = Console(file=StringIO(), force_terminal=True)


FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger(__name__)


app = typer.Typer(no_args_is_help=True)


def _parse_rfc3339(s: str) -> datetime:
    return datetime.fromisoformat(s)


_datasworn._parse_rfc3339 = _parse_rfc3339

RULESETS = [
    "classic",
    "delve",
    "starforged",
    "starsmith",
    "sundered_isles",
]

index: dict[str, Any] = {}
id_tree: dict[str, dict] = {}
rules: dict[str, _datasworn.RulesPackage] = {}


def add_to_index(ids, index, obj):
    ids_ = ids
    if hasattr(obj, "id"):  # and isinstance(obj.id, IDType):
        key = str(obj.id.value)
        if key in index:
            msg = f"Duplicate key {key} in index"
            raise KeyError(msg)
        index[key] = obj
        ids[key] = {}
        ids_ = ids[key]

    match obj:
        case obj if is_dataclass(obj):
            for field in fields(obj):
                # if hasattr(obj, field):
                vv = getattr(obj, field.name)
                add_to_index(ids_, index, vv)

        case dict():
            for field, v in obj.items():
                add_to_index(ids_, index, v)

        case list():
            for v in obj:
                add_to_index(ids_, index, v)


class RulesServer:
    def load_rules(self, ruleset_path: str) -> _datasworn.RulesPackage:
        path = Path(__file__).parent.absolute()
        with Path(path / ruleset_path).open("rt") as file:
            rules_dict = json.loads(file.read())
        return rules_dict

    def _load_ruleset(self, ruleset: str):
        log.debug(f"Loading ruleset: {ruleset}")
        rules = self.load_rules(ruleset + ".json")
        return _datasworn.RulesPackage.from_json_data(rules)

    def __init__(self) -> None:
        global rules
        rules = {}
        t0 = time.perf_counter()
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self._load_ruleset, ruleset): ruleset
                for ruleset in RULESETS
            }
            # for ruleset in RULESETS:
            for future in as_completed(futures):
                ruleset = futures[future]
                try:
                    rules_package = future.result()
                except Exception as exc:
                    print(f"{ruleset} generated an exception: {exc}")
                else:
                    # add individual rules to global index
                    add_to_index(id_tree, index, rules_package)
                    rules[rules_package.id.value] = rules_package
        t1 = time.perf_counter()
        log.debug(f"Loaded rules in {t1 - t0:.2f} seconds")


def get_parent_id(id_, node=id_tree):
    for k, v in node.items():
        if id_ in v:
            return k
        parent = get_parent_id(id_, v)
        if parent:
            return parent
    return None
    # print(v)


def get_rule_types():
    rule_types = {}

    def _recurse(s: list):
        if len(s) == 1:
            return None
        return {s.pop(0): _recurse(s)}

    for k in index:
        sk = k.split(":")[0]  # .split(".")
        # rule_types[sk[0]] = _recurse(sk[1:]) if len(sk) > 1 else None
        rule_types[sk] = None

    return rule_types


@app.command()
def count(
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Count IDs by prefix."""
    counts = []
    counts_by_ruleset = defaultdict(list)

    for k, v in index.items():
        # if "row" in k:
        #     continue
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

    # table = Table("ID Prefix", "Count")
    # for k, v in Counter(counts).most_common():
    #     table.add_row(k, repr(v))
    # print(table)

    table = Table("ID Prefix", "Total", *RULESETS)
    # for k, v in Counter(counts).most_common():
    for t in Counter(counts).most_common():
        # print(t)
        k = t[0]
        v = t[1]
        # row = []
        # print (k, v)
        table.add_row(
            k,
            repr(v),
            *[repr(counts_by_ruleset[ruleset].count(k)) for ruleset in RULESETS],
        )
        # for ruleset in RULESETS:
        #     row.append()
        # table.add_row(k, *row)

        # table.add_row(k, repr(v))
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
):
    for k in index.keys():
        if skip_rows and ".row:" in k:
            continue
        if not parents:
            print(k)
        else:
            print(f"{k} --> {get_parent_id(k)}")

    # print(id_tree)


@app.command()
def dump():
    # print(Inspect(rules, max_depth=1, max_length=1, max_string=10))
    # print(vars(rules))
    # inspect(rules._re)
    # with console.capture() as capture:
    for ruleset in rules:
        print(Rule(ruleset))
        # console.print(Inspect(rules[ruleset], max_depth=1, max_length=1, max_string=100))
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


RulesServer()

if __name__ == "__main__":
    app()
