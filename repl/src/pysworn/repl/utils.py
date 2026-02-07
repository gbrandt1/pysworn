import logging
import re
from collections import ChainMap, UserDict
from collections.abc import Mapping
from functools import reduce
from typing import Any

from pysworn.common import datasworn_tree
from rich import print

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

                _depth_first_update(target.setdefault(k, {}), v)

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
    include: str | None = None, exclude: str | None = None
) -> dict[str, Any]:
    id_tree: dict[str, Any] = {}
    for id_ in index:
        if include and include not in id_:
            continue
        if exclude and exclude in id_:
            continue
        # if "/" not in id_:
        #     log.warning(f"Skipping {id_}")
        #     continue
        tag, path = id_.split(":")

        if tag.endswith(".row"):
            continue

        # tag = tag.split(".")[0]
        # path_ = path.replace(".", "/").split("/")
        path_ = re.split(r"[\./]", path)
        path_.insert(1, tag)
        # path_.append(id_)

        # print(f"{path_}")
        # print(nested_ids)
        d = id_tree
        for k in path_:
            # if not isinstance(d, dict):
            #     log.warning(f"Skipping {id_} for {d}")
            #     break
            d = d.setdefault(k, {})
            # d = reduce(lambda d, k: d.setdefault(k, {}), path_[:-1], nested_ids)
        # if isinstance(d, dict):
        d["id"] = id_
        # else:
        #     log.warning(f"Skipping {id_} for {d}")

    print(id_tree)

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


def fuzzy_search(key: list[str], paths: dict[str, str]) -> str | None:
    from pysworn.repl.fuzzy import Matcher
    from rich.style import Style

    keys = " ".join(key)

    log.debug(f"looking for '{keys}' in {len(paths)} paths")

    matcher = Matcher(keys, match_style=Style(bold=True), case_sensitive=False)
    matches: list[Any] = []
    for p in paths.keys():
        score = matcher.match(p)
        if score > 0.0:
            matches.append((matcher.match(p), p, paths[p]))

    if len(matches) == 0:
        log.error("No fuzzy matches found.")
        return None

    matches.sort(reverse=True)
    matches = [m for m in matches if m[0] > 10.0]
    log.debug(matches)

    if len(matches) == 1 or matches[0][0] > matches[1][0]:
        winner = matches[0][2]
        log.debug(f"Fuzzy winner: {winner}")
        return winner

    from rich.table import Table

    print("\nDid you mean:\n")
    t = Table.grid(padding=(0, 1), expand=True)
    t.add_column(justify="left", overflow="fold")
    t.add_column(justify="right", style="log.path")
    for m in matches:
        path = m[2].split(":")[1].replace("_", " ").title().split("/")
        path[-1] = path[-1].replace(".", ", ")
        path_ = " > ".join(path[1:]) + f" ({path[0]})"

        t.add_row(matcher.highlight(m[1]), path_)
    print(t)
    return None
