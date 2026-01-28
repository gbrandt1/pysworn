import logging
from collections import ChainMap
from collections.abc import Mapping
from string import Template
from typing import Any

from pysworn.common import datasworn_tree
from rich import print

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


def get_id_dict(*chain: list[str]) -> dict[str, Any]:
    nested_ids: dict[str, Any] = {}
    for id_ in index:
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

    # print(nd)
    return nested_ids

    cm = DeepChainMap(*[nested_ids[c] for c in chain])

    def _attach(d: dict[str, Any], path: list[str] = []):
        for k, v in d.items():
            path_ = path + [k]
            if len(v) == 0:
                # ids = fnmatch.filter(list(index), "".join(path_))
                d[k] = Template(f"{path_[0]}:$ruleset/{'/'.join(path_[1:])}")
            else:
                _attach(v, path_)

    merged_dict = cm.to_dict()
    for k, v in merged_dict.items():
        _attach(v, [k])  # , f"{k}:*")

    return merged_dict
