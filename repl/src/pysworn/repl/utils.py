from collections import ChainMap
from collections.abc import Mapping
from string import Template
from typing import Any

from pysworn.common import datasworn_tree

index = datasworn_tree.index


def _depth_first_update[K, V](
    target: dict[K, V],
    source: Mapping[K, V],
) -> None:
    for k, v in source.items():
        if not isinstance(v, Mapping):
            target[k] = v
            continue

        _depth_first_update(target.setdefault(k, {}), v)


class DeepChainMap[K, V](ChainMap[K, V]):
    """A recursive subclass of ChainMap"""

    def __getitem__(self, k: K) -> V:
        submaps = [m for m in self.maps if k in m]
        if not submaps:
            return self.__missing__(k)
        if isinstance(submaps[0][k], Mapping):
            return DeepChainMap(*(submap[k] for submap in submaps))
        return super().__getitem__(k)

    def to_dict(self) -> dict[K, V]:
        d: dict[K, V] = {}
        for m in reversed(self.maps):
            _depth_first_update(d, m)
        return d


def get_merged_dict(chain: list[str]):
    nd = {}
    for id_ in index:
        if "/" not in id_:
            continue
        tag, path = id_.split(":")
        if tag in ("oracle_rollable", "move", "asset", "npc", "truth", "atlas_entry"):
            path = path.split("/")
            path.insert(1, tag)

        d = nd
        for k in path:
            d = d.setdefault(k, {})

    cm = DeepChainMap(*[nd[c] for c in chain])

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
