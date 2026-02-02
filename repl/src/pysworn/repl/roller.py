import logging
import random
from collections.abc import Generator
from dataclasses import dataclass
from inspect import getfullargspec
from typing import (
    Any,
    ClassVar,
    TypeAliasType,
    Union,
    get_args,
    get_origin,
)

from datasworn.core.models import (
    BaseModel,
    OracleColumnText,
    OracleColumnText2,
    OracleColumnText3,
    OracleRoll,
    OracleTablesCollection,
    OracleTableSharedRolls,
    OracleTableSharedText,
    OracleTableSharedText2,
    OracleTableText,
    OracleTableText2,
    OracleTableText3,
)
from pysworn.renderables import get_renderable
from rich.console import Group
from rich.table import Table

# from rich.console import Console
# console = Console()

log = logging.getLogger(__name__)


@dataclass
class RollResult:
    roll: int
    obj: Any
    plain: bool = False

    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ):
        if self.plain:
            yield get_renderable(self.obj)
            return

        path = self.obj.id.split(":")[1].replace("_", " ").title().split("/")
        path[-1] = path[-1].replace(".", ", ")
        path_ = " > ".join(path[1:]) + f" ({path[0]})"

        t = Table.grid(padding=(0, 1), expand=True)
        t.add_column(justify="right", width=4)
        t.add_column(ratio=1, overflow="fold")
        t.add_column(style="log.path")
        t.add_row(f"[b]{self.roll}[/]:", f"{self.obj.text}", path_)

        yield t


def get_roller(v: BaseModel, *args: Any, **kwargs: Any) -> RenderableType:
    rollable_type = Roller.Registry.get(type(v))
    log.debug(f"Roller for type: {type(v)} -> {rollable_type}")

    if not rollable_type:
        return f"Can't roll on {type(v)}"

    results: list[RollResult] = []

    rollable = rollable_type(v, *args, **kwargs)

    def _flatten(r, level: int = 0):
        # log.debug(f"{r}")
        for r_ in r:
            if isinstance(r_, RollResult):
                # console.print(Padding(r_, pad=(0, 0, 0, level * 4)))
                # console.print(r_)
                results.append(r_)
            elif isinstance(r_, Roller):
                _flatten(r_, level + 1)
            else:
                log.error(f"Unknown rollable result: {r_}")

    _flatten(rollable)

    return Group(*results)


class Roller(Generator):
    """Base class for all Rollers.

    A Roller is a generator that yields RollResults.

    This class should be subclassed for each rollable type.
    It automatically registers subclasses based on the type annotations
    of the __init__ method.
    """

    Registry: ClassVar[dict[type, type]] = {}

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)

        fullargspec = getfullargspec(cls.__init__)
        for k, v in fullargspec.annotations.items():
            log.debug(f"{k}: {v.__class__} {v}")
            cls._resolve_type(v)

    @classmethod
    def _resolve_type(cls, arg: type | TypeAliasType):
        if isinstance(arg, TypeAliasType):
            v = get_args(arg.__value__)[0]
        else:
            v = arg
        if get_origin(v) is Union:
            for arg in get_args(v):
                cls._resolve_type(arg)
        else:
            if v in Roller.Registry:
                raise KeyError(f"Duplicate renderable type: {v}")
            if v.__module__ == "datasworn.core.models":
                Roller.Registry[v] = cls
                log.debug(f"{v}: {cls}")

    def __init__(self, obj: BaseModel, *args: Any, **kwargs: Any):
        self.obj = obj

    def send(self, *args: Any, **kwargs: Any) -> Any:
        raise StopIteration

    def throw(self, type_=None, value=None, traceback=None) -> Any:
        super().throw(type_, value, traceback)


class CollectionRoller(Roller):
    def __init__(
        self,
        collection: OracleTablesCollection
        | OracleTableSharedRolls
        | OracleTableSharedText
        | OracleTableSharedText2,
        # | NpcCollection
        # | AssetCollection
        # | AtlasCollection,
        *args: Any,
        **kwargs: Any,
    ):
        self.collection = collection
        self.content = iter(self.collection.contents.values())
        if hasattr(self.collection, "collections"):
            self.collections = iter(self.collection.collections.values())
        self.args = args
        self.kwargs = kwargs

    def send(self, *args: Any, **kwargs: Any) -> Any:
        if v := next(self.content):
            return OracleRoller(v, *self.args, **self.kwargs)
        if not self.collections:
            raise StopIteration
        if v := next(self.collections):
            return CollectionRoller(v, *self.args, **self.kwargs)
        raise StopIteration


class OracleRoller(Roller):
    def __init__(
        self,
        oracle: OracleTableText
        | OracleTableText2
        | OracleTableText3
        | OracleColumnText
        | OracleColumnText2
        | OracleColumnText3,
        *args: Any,
        **kwargs: Any,
    ):
        self.oracle = oracle
        self.dice = int(self.oracle.dice.split("d")[1])
        self.number_of_rolls = getattr(self.oracle, "number_of_rolls", 1)
        self.args = args
        self.kwargs = kwargs

    def _oracle_rolls(self, oracle_rolls: list[OracleRoll]):
        for oracle_roll in oracle_rolls:
            number_of_rolls = getattr(oracle_roll, "number_of_rolls", 1)
            for n in range(number_of_rolls):
                try:
                    oracle = datasworn_tree.index[oracle_roll.oracle]
                    yield from OracleRoller(oracle)()
                except KeyError:
                    log.error(f"Unknown oracle: {oracle_roll.oracle} in {oracle_rolls}")

    def send(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> RollResult:
        if self.number_of_rolls == 0:
            raise StopIteration
        self.number_of_rolls -= 1
        roll = random.randint(1, self.dice)
        row = None
        for row in self.oracle.rows:
            if row.roll and row.roll.min <= roll <= row.roll.max:
                # if oracle_rolls := row.oracle_rolls:
                #     yield from self._oracle_rolls(oracle_rolls)
                # else:
                break
        return RollResult(roll=roll, obj=row, **self.kwargs)


# class OracleRollable
if __name__ == "__main__":
    from pysworn.common import datasworn_tree
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.padding import Padding

    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )

    console = Console()
    console.print(Roller.Registry)

    # for k in datasworn_tree:
    #     datasworn_tree[k]
    datasworn_tree["starforged"]

    for k, v in datasworn_tree.index.items():
        if not k.startswith("oracle_collection:"):
            continue
        if rollable := get_roller(v, plain=False):
            log.debug(f"'{k}'")
            # roll, r = rollable()

            def _flatten(r, level: int = 0):
                log.debug(f"{r}")
                for r_ in r:
                    if isinstance(r_, RollResult):
                        console.print(Padding(r_, pad=(0, 0, 0, level * 4)))
                    elif isinstance(r_, Roller):
                        _flatten(r_, level + 1)
                    else:
                        log.error(f"Unknown rollable result: {r_}")

            _flatten(rollable)
