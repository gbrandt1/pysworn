import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import fields, is_dataclass
from datetime import datetime

# from io import StringIO
from pathlib import Path
from typing import Any

import orjson as json
import pysworn.datasworn._datasworn as _datasworn
import typer
from rich import print
from rich.console import Console
from rich.traceback import install

from ._datasworn import *  # noqa

install()

console = Console()
# console = Console(file=StringIO(), force_terminal=True)


# FORMAT = "%(message)s"
# logging.basicConfig(
#     level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
# )
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


class ParsedId:
    def __init__(self, id_: str):
        self.rule_type = None
        self.ruleset = None
        self.category = None
        if ":" in id_:
            self.rule_type, path = id_.split(":")
            self.ruleset, self.category, *_ = path.split("/")
        elif id_ in RULESETS:
            self.ruleset = id_
            self.rule_type = "source"
        else:
            pass

    # def __str__(self):
    #     return f"{self.rule_type}:{self.ruleset}/{self.category}"

    def __repr__(self):
        return f"<ParsedId {self.rule_type}:{self.ruleset}/{self.category}>"


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
        with Path(path / "_datasworn" / ruleset_path).open("rt") as file:
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


def breadcrumbs(id_: str) -> list[str]:
    parsed_id = ParsedId(id_)
    if not parsed_id.category:
        if parsed_id.ruleset:
            return [parsed_id.ruleset]
        return [""]
    parts = []  # [parsed_id.ruleset, parsed_id.category]
    next_id = id_
    while next_id:
        obj = index[next_id]
        if hasattr(obj, "name") and obj.name:
            parts.append(obj.name.value)
        elif hasattr(obj, "label") and obj.label:
            parts.append(obj.name.value)
        else:
            break
        next_id = get_parent_id(next_id)
    parts.append(parsed_id.category)
    parts.append(parsed_id.ruleset)
    parts.reverse()
    print(parts)
    return parts


RulesServer()
