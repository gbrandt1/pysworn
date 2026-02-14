from dataclasses import dataclass
from .tree import DataswornTree, datasworn_tree

from datasworn.core.models import Truth


@dataclass
class Truths:
    truths: list[Truth]


__all__ = ["DataswornTree", "datasworn_tree"]
