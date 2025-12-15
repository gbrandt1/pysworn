import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import fields, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import orjson as json
import pysworn.datasworn._datasworn as _datasworn
import typer
from rich import print
from rich.console import Console

from ._datasworn import *  # noqa
from .logging import log

console = Console()


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
    # "ancient_wonders",
    "fe_runners",
]

TYPE_TITLES = {
    "asset": "Assets",
    "asset.ability": "Assets Abilities",
    "asset.ability.move": "Assets Ability Moves",
    "asset.ability.oracle_rollable": "Assets Ability Oracles",
    "asset.ability.oracle_rollable.row": "Assets Ability Oracle Rows",
    "asset_collection": "Assets",
    "atlas_collection": "Atlas",
    "atlas_entry": "Atlas",
    "classic": "Ironsworn",
    "delve": "Delve",
    "delve_site": "Sites",
    "delve_site.denizen": "Site Denizens",
    "delve_site_domain": "Domains",
    "delve_site_domain.danger": "Domain Dangers",
    "delve_site_domain.feature": "Domain Features",
    "delve_site_theme": "Themes",
    "delve_site_theme.danger": "Theme Dangers",
    "delve_site_theme.feature": "Theme Features",
    "move": "Moves",
    "move.oracle_rollable": "Move Oracles",
    "move.oracle_rollable.row": "Move Oracle Rows",
    "move_category": "Moves",
    "npc": "NPCs",
    "npc.variant": "NPC Variants",
    "npc_collection": "NPCs",
    "oracle_collection": "Oracles",
    "oracle_rollable": "Oracles",
    "oracle_rollable.row": "Oracle Rows",
    "rarity": "Rarities",
    "starforged": "Starforged",
    "starsmith": "Starsmith",
    "sundered_isles": "Sundered Isles",
    "truth": "Truths",
    "truth.option": "Truth Options",
    "truth.option.oracle_rollable": "Truth Option Oracles",
    "truth.option.oracle_rollable.row": "Truth Option Oracle Rows",
    "rules": "Rules",
    "source": "Source",
    # "ancient_wonders": "Ancient Wonders",
    "fe_runners": "FE Runners",
}


index: dict[str, Any] = {}
id_tree: dict[str, dict] = {}
rules: dict[str, _datasworn.RulesPackage] = {}


class ParsedId:
    ruleset: str

    def __init__(self, id_: str) -> None:
        self.id: str = id_
        self.type: str = "ruleset"
        self.ruleset: str
        self.category: str | None = None
        self.subcategory: str | None = None

        if id_.startswith("datasworn:"):
            id_ = id_[10:]

        if ":" in id_:
            self.type, path = id_.split(":")
            if len(pp := path.split("/")) < 3:
                self.ruleset, self.category = pp
            else:
                self.ruleset, self.category, self.subcategory, *_ = pp
        elif id_ in RULESETS:
            self.ruleset = id_
            self.type = "source"
        else:
            msg = f"Could not parse id: {id_}"
            raise KeyError(msg)

        if self.category:
            self.category = self.category.split(".")[0]

        if self.subcategory:
            self.subcategory = self.subcategory.split(".")[0]
        else:
            pass

    def __repr__(self):
        return f"<ParsedId {self.type}:{self.ruleset}/{self.category}>"

    def __rich__(self):
        return (
            f"'{self.id}' --> {' > '.join(breadcrumbs(self.id))} "
            # f"<{self.type=} {self.ruleset=} {self.category=} {self.subcategory=}>"
        )


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
        self.rules = {}
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
                    self.rules[rules_package.id.value] = rules_package
        t1 = time.perf_counter()
        log.debug(f"Loaded {len(self.rules)} rulesets in {t1 - t0:.2f} seconds")


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


def breadcrumbs(id_) -> list[str]:
    def _get_name_or_label(id_):
        obj = index[id_]
        if hasattr(obj, "name") and obj.name:
            return obj.name.value
        elif hasattr(obj, "label") and obj.label:
            return obj.label.value
        elif "." in id_:
            return id_.split(".")[-1]
        else:
            return id_

    parts = []
    next_id = id_
    if name := _get_name_or_label(next_id):
        parts.append(f"**{name.upper()}**")
    next_id = get_parent_id(next_id)
    while next_id:
        if next_id in RULESETS:
            break
        if name := _get_name_or_label(next_id):
            parts.append(f"[{name}]({next_id})")
        else:
            break
        next_id = get_parent_id(next_id)

    parsed_id = ParsedId(id_)

    parts.append(
        f"[{TYPE_TITLES[parsed_id.type]}]({parsed_id.ruleset}.{parsed_id.type})"
    )
    parts.append(f"[{TYPE_TITLES[parsed_id.ruleset]}]({parsed_id.ruleset})")
    parts.reverse()
    # print(parts)
    return parts


rules = RulesServer().rules
