import logging
import re
from collections import ChainMap, UserDict
from collections.abc import Mapping
from doctest import ELLIPSIS_MARKER
from typing import Any

from pysworn.common import datasworn_tree
from pysworn.repl.state import state
from pysworn.repl.theme import pysworn_theme
from rich.console import Console, RenderableType
from rich.text import Text

console = Console(theme=pysworn_theme)
print = console.print

log = logging.getLogger(__name__)
index = datasworn_tree.index


class ReadOnlyChainmap(UserDict[str, Any]):
    """Combine multiple mappings for sequential lookup.

    Source: https://code.activestate.com/recipes/305268/
    """

    def __init__(self, *maps: Mapping[str, Any]) -> None:
        self._maps: tuple[Mapping[str, Any], ...] = maps

    def __getitem__(self, key: str):
        for mapping in self._maps:
            try:
                return mapping[key]
            except KeyError:
                pass
        raise KeyError(key)


class DeepChainMap[K, V](ChainMap[K, V]):
    """A recursive subclass of ChainMap"""

    def __getitem__(self, k: K) -> V:
        submaps = [submap for submap in self.maps if k in submap]
        if not submaps:
            return self.__missing__(k)
        if isinstance(submaps[0][k], Mapping):
            return DeepChainMap(*(submap[k] for submap in submaps))
        return super().__getitem__(k)

    def to_dict(self) -> dict[K, V]:
        def _depth_first_update(
            target: dict[K, V],
            source: Mapping[K, V],
        ) -> None:
            for k, v in source.items():
                if not isinstance(v, Mapping):
                    target[k] = v
                    continue
                if k not in target:
                    target[k] = {}
                _depth_first_update(target[k], v)

        d: dict[K, V] = {}
        for m in reversed(self.maps):
            _depth_first_update(d, m)
        return d


def get_chain_map(*chain: dict[str, Any]) -> DeepChainMap[str, Any]:
    return DeepChainMap[str, Any](*chain)


def depth_first_merge(*chain: dict[str, Any]) -> dict[str, Any]:
    return DeepChainMap[str, Any](*chain).to_dict()


def get_nested_dict(index: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for _id in index:
        if ":" not in _id or "." in _id.split(":")[1]:
            continue
        *nodes, last = (_id.split(":")[1]).split("/")
        d = result
        for k in nodes:
            d = d.setdefault(k, {})
        d[last] = {}
    return result


def get_id_tree(
    include: str | None = None,
    exclude: str | None = None,
) -> dict[str, Any]:
    id_tree: dict[str, Any] = {}
    for id_ in index:
        log.debug(f"Processing id: {id_}")
        if include and include not in id_:
            continue
        if exclude and exclude in id_:
            continue
        tag, path = id_.split(":")

        if tag.endswith(".row"):
            continue

        path_ = re.split(r"[\./]", path)
        path_.insert(1, tag)

        d = id_tree
        for k in path_:
            d = d.setdefault(k, {})
        d["id"] = id_

    # log.debug(id_tree)

    return id_tree


def depth_first_search(
    d: dict[str, Any],
    key: list[str],
) -> list[Any]:
    # print(d.keys())
    log.debug(f"Searching for {key}")

    paths = []

    def _find_leaves(d: dict[str, Any], path: list[str] = []):
        for k, v in d.items():
            path_ = path + [k]
            # log.debug(f"Visiting: {path_} --> {type(v)}")
            if isinstance(v, dict):
                _find_leaves(v, path_)
            else:
                # if "." not in path_[-1]:
                #     log.debug(f"Leaf: {path_[-1]}")
                if k == key[-1]:
                    log.debug(f"Candidate: {path_}")
                    paths.append(path_)

    _find_leaves(d)
    log.debug(f"Found paths: {paths}")

    for i, k in enumerate(key[::-1], 1):
        paths = [p for p in paths if p[-i] == k]
        log.debug(f"{i} {k}: {paths}")

    return paths


def get_flat_paths():
    paths: dict[str, str] = {}
    for k in index:
        tag, path = k.split(":")
        if "." in path:
            continue
        path = path.split("/")
        path = " ".join(reversed([path[0]] + [tag] + path[1:]))
        path = path.replace("_", " ")
        paths[path] = k

    return paths


def id_to_tokens(id_: str):
    tag, path = id_.split(":")
    path = path.split("/")
    path = " ".join(reversed([path[0]] + [tag] + path[1:]))
    path = path.replace("_", " ")
    return path


def build_human_path(path: list[str]) -> str | None:
    """Transform id path to human typeable path"""
    seen = set()
    path_dd: dict[str, Callable[[list[str]], Any]] = {
        # ASSETS
        "asset": lambda p: p,
        "asset.ability": lambda p: None,  # rollable
        "asset.ability.move": lambda p: ["move"] + p[1:-2] + p[-1:],
        "asset.ability.move.condition": lambda p: (
            None
        ),  # TODO: extract options from move
        "asset.ability.move.outcome": lambda p: None,  # ,["move"] + p[1:-3] + p[-2:],
        "asset.ability.oracle_rollable": lambda p: ["oracle"] + p[1:-2] + p[-1:],
        # "asset.ability.oracle_rollable.row": lambda p: None,  # rollable
        "asset_collection": lambda p: ["assets"] + p[1:],
        # ATLAS
        "atlas_collection": lambda p: p,
        "atlas_entry": lambda p: p,
        # DELVES
        "delve_site": lambda p: p,
        "delve_site.denizen": lambda p: None,  # rollable (TODO)
        "delve_site_domain": lambda p: ["domain"] + p[1:],
        "delve_site_domain.danger": lambda p: None,  # rollable (TODO)
        "delve_site_domain.feature": lambda p: None,  # rollable (TODO)
        "delve_site_theme": lambda p: ["theme"] + p[1:],
        "delve_site_theme.danger": lambda p: None,  # rollable (TODO)
        "delve_site_theme.feature": lambda p: None,  # rollable (TODO)
        # MOVES
        "move": lambda p: p,
        "move.condition": lambda p: None,  # TODO: extract options from move
        "move.oracle_rollable": lambda p: ["move_oracle"] + p[1:],
        "move.oracle_rollable.row": lambda p: None,  # rollable
        "move.outcome": lambda p: None,  # ["move"] + p[1:],
        "move_category": lambda p: ["moves"] + p[1:],
        # NPCS
        "npc": lambda p: p,
        "npc.variant": lambda p: ["npc"] + p[1:-2] + p[-1:],
        "npc_collection": lambda p: ["npcs"] + p[1:],
        # ORACLES
        "oracle_collection": lambda p: ["oracles"] + p[1:],
        "oracle_rollable": lambda p: ["oracle"] + p[1:],
        "oracle_rollable.row": lambda p: None,  # rollable
        # RARITIES
        "rarity": lambda p: p,
        # TRUTHS
        "truth": lambda p: p,
        "truth.option": lambda p: None,  # rollable
        "truth.option.oracle_rollable": lambda p: ["oracle"] + p[1:-2] + p[-1:],
        "truth.option.oracle_rollable.row": lambda p: None,  # rollable
    }
    try:
        path_ = path_dd[path[1]](path[1:])
    except KeyError:
        msg = f"Unknown type: {path[1]}"
        raise ValueError(msg)
    if not path_:
        # log.debug(f"Skipping {path}")
        return None
    p = reversed([p for p in path_])
    p = " ".join(p)  # + f" {path[0]}"

    p = p.replace(".", " ")
    log.debug(f"{path} --> {p}")
    if p in seen:
        log.warning(f"seen: {seen}")
        p.append(path[0])
        log.warning(f"{path} --> {p}")
    seen.add(p)
    return p


def add_ruleset(ruleset: str):
    if ruleset in state["rulesets"]:
        log.warning("Already playing: %s", ", ".join(state["rulesets"]))
        return
    log.info(f"Adding ruleset: {ruleset}")
    state["rulesets"] = [ruleset] + state["rulesets"]

    # idd = {p: get_id_tree(p)[p] for p in state["rulesets"]}
    # merged = depth_first_merge(*idd.values())
    # state["tree"] = merged
    log.debug(f"{state['rulesets']}")
    id_tree = get_id_tree(ruleset)
    # print(id_tree)
    state["tree"] |= id_tree

    merged = state["tree"]  # depth_first_merge(*state["tree"].values())
    paths = {}

    def _flatten_id_tree(tree: dict[str, Any], path: list[str] = []):
        for k, v in tree.items():
            if isinstance(v, dict):
                _flatten_id_tree(v, path + [k])
            else:
                if p := build_human_path(path):
                    if p in paths:
                        msg = f"Duplicate path: '{p}' --> '{paths[p]}'"
                        log.warning(msg)
                        old_ruleset = paths[p].split(":")[1].split("/")[0]
                        paths[p + " " + old_ruleset] = paths[p]
                        # raise ValueError(msg)
                    else:
                        log.debug(f"Adding path: '{p}' --> '{v}'")
                    paths[p] = v

    _flatten_id_tree(merged)
    state["paths"] |= paths


def fuzzy_search(key: list[str], paths: dict[str, str]) -> RenderableType | str:
    from pysworn.repl.fuzzy import Matcher
    from rich.style import Style

    keys = " ".join(key)

    log.debug(f"looking for '{keys}' in {len(paths)} paths")

    matcher = Matcher(
        keys,
        match_style=Style.parse("bold bright_cyan"),
        case_sensitive=False,
    )
    matches: list[Any] = []
    for p in paths.keys():
        score = matcher.match(p)
        if score > 1.0:
            id_ = paths[p]
            matches.append((score, p, id_))

    if len(matches) == 0:
        msg = "No fuzzy matches found."
        raise ValueError(msg)

    matches.sort(reverse=True)
    matches = [m for m in matches if m[0] > 0.0]  # [:10]
    if len(matches) == 0:
        msg = "No fuzzy matches found."
        raise ValueError(msg)

    for m in matches:
        log.debug(m)

    if len(matches) == 1 or matches[0][0] > matches[1][0]:
        winner = matches[0][2]
        log.debug(f"Fuzzy winner: {winner}")
        # print(Text(matches[0][1], style="yellow"))
        return winner

    from rich.table import Table

    t = Table(
        title="Did you mean:",
        title_justify="left",
        padding=(0, 1),
        expand=True,
        show_header=False,
        # show_edge=False,
        # show_lines=False,
        box=None,
        border_style="scope.border",
    )
    t.add_column(ratio=1)
    t.add_column(justify="right", style="log.path")
    for m in matches:
        # path = m[2].split(":")[1].replace("_", " ").title().split("/")
        # path[-1] = path[-1].replace(".", ", ")
        # path_ = " > ".join(path[1:]) + f" ({path[0]})"
        path_ = m[2]

        h = matcher.highlight(m[1])
        t.add_row(
            h,
            Text(path_, style="log.path"),
        )
    return t
