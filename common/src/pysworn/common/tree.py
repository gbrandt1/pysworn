import datetime
import enum
import logging
from collections import ChainMap, OrderedDict
from collections.abc import Mapping
from importlib.resources import files
from typing import Any

from datasworn.core.models import Expansion, Ruleset
from pydantic import AnyUrl, BaseModel
from rich import print

# from rich.logging import RichHandler
# FORMAT = "%(message)s"
# logging.basicConfig(
#     level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
# )

log = logging.getLogger(__name__)

DATASWORN_JSON_SOURCES: dict[str, tuple[str, type[Expansion] | type[Ruleset]]] = {
    "classic": ("datasworn", Ruleset),
    "delve": ("datasworn", Expansion),
    "starforged": ("datasworn", Ruleset),
    "sundered_isles": ("datasworn", Expansion),
    "ancient_wonders": ("datasworn_community_content", Expansion),
    "fe_runners": ("datasworn_community_content", Expansion),
    "starsmith": ("datasworn_community_content", Expansion),
}


class DataswornTree(Mapping[str, Any]):
    """Lazy loading and self-indexing Datasworn ruleset and expansion tree."""

    def __init__(self) -> None:
        self._json_sources = DATASWORN_JSON_SOURCES
        self._sources: dict[str, Any] = {}
        self.index: OrderedDict[str, BaseModel] = {}
        self.human_index: OrderedDict[str, BaseModel] = {}

    def __getitem__(self, name: str):
        if name not in self._json_sources:
            msg = f"Source must be one of {list(self._json_sources.keys())} not {name}."
            raise KeyError(msg)
        if name not in self._sources:
            self._load_source(name, *self._json_sources.__getitem__(name))
        return self._sources.__getitem__(name)

    def __iter__(self):
        return iter(self._json_sources)

    def __len__(self):
        return len(self._json_sources)

    def _load_source(
        self, name: str, scope: str, type_: type[Expansion] | type[Ruleset]
    ) -> None:
        json_source = files(f"{scope}.{name}").joinpath(f"json/{name}.json").read_text()
        self._sources[name] = type_.model_validate_json(json_source)
        self._build_index(self._sources[name])
        self._build_human_index()
        log.debug(f"Loaded {name}")

    def _build_index(
        self,
        obj: BaseModel | dict[str, Any] | list[Any],
        path: str = "",
    ) -> int:
        """Datasworn ids --> Datasworn objects"""
        num = 0
        match obj:
            case BaseModel():
                _id = getattr(obj, "id", None)
                if not _id:
                    _id = getattr(obj, "_id", None)
                if _id:
                    self.index[_id] = obj

                    num += 1
                for k, v in obj:
                    self._build_index(v, path=f"{path}.{k}")
            case dict():
                # last = path.split(".")[-1]
                # if last not in (
                #     "contents",
                #     "collections",
                #     "oracles",
                #     "controls",
                #     "variants",
                #     "moves",
                #     "options",
                #     "trigger",
                # ):
                #     log.debug(f"{path}: {type(obj)}")
                for k, v in obj.items():
                    self._build_index(v, path=f"{path}['{k}']")
            case list():
                for k, v in enumerate(obj):
                    self._build_index(v, path=f"{path}[{k}]")
            case int() | str() | None | datetime.date() | enum.Enum() | AnyUrl():
                pass
            case _:
                log.error(f"{path}: Unknown type: {type(obj)}")
        return num

    def _build_human_index(self):
        """Index using humandreadable Datasworn paths --> Datasworn objects"""
        for k, v in self.index.items():
            if ":" not in k:
                continue
            tag, path = k.split(":")
            if "." in path:
                continue
            if "." in tag:
                tag = tag.split(".")[0]
            # if tag.startswith("oracle"):
            #     tag = "oracle"
            if "_" in tag:
                tag = tag.split("_")[0]
            path = path.split("/")
            path.insert(1, tag)
            path = " ".join(path).replace("_", "-")  # .title()
            self.human_index[path] = v


datasworn_tree = DataswornTree()


if __name__ == "__main__":
    from rich.console import Console

    console = Console(force_terminal=True)
    # for k in datasworn_tree:
    k = "starforged"
    t = datasworn_tree[k]
    console.print(t)
