import logging
from collections import ChainMap
from collections.abc import Mapping
from typing import Any

from pysworn.common import datasworn_tree
from rich import print
from rich.text import Text

log = logging.getLogger(__name__)
index = datasworn_tree.index


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


def get_id_dict(include: str, exclude: str) -> dict[str, Any]:
    nested_ids: dict[str, Any] = {}
    for id_ in index:
        if include not in id_:
            continue
        if exclude in id_:
            continue
        if "/" not in id_:
            log.warning(f"Skipping {id_}")
            continue
        tag, path = id_.split(":")
        # if tag in ("oracle_rollable", "move", "asset", "npc", "truth", "atlas_entry"):
        path_ = path.split("/")
        path_.insert(1, tag)

        d = nested_ids
        for k in path_:
            d = d.setdefault(k, {})

    def _expand(d: dict[str, Any], path: list[str] = []):
        for k, v in d.items():
            p = path.copy()
            p.append(k)
            if v == {}:
                id_ = f"{p[1]}:{p[0]}/{'/'.join(p[2:])}"
                d[k] = id_  # f"<{type(index[id_]).__name__}>"
            else:
                _expand(v, p)

    _expand(nested_ids)
    return nested_ids


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


def fuzzy_search(key: list[str], paths: dict[str, str]) -> str | None:
    from pysworn.repl.fuzzy import Matcher
    from rich.style import Style

    # paths = get_flat_paths()
    # paths = depth_first_search(paths, key)

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

    print("\nDid you mean:\n")
    for m in matches:
        print(matcher.highlight(m[1]).append_text(Text(f"-->{m[2]}", style="cyan")))
    print()

    return None
