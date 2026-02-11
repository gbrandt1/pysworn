import logging
import random
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
from unittest import result
from webbrowser import get

from datasworn.core.models import (
    Asset,
    AssetCollection,
    AtlasCollection,
    BaseModel,
    DelveSite,
    EmbeddedOracleColumnText,
    EmbeddedOracleRollable,
    EmbeddedOracleTableText,
    MoveActionRoll,
    NpcCollection,
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
    Truth,
)
from pysworn.renderables import get_renderable
from rich.console import (
    Console,
    ConsoleOptions,
    RenderableType,
    RenderResult,
)
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
    ) -> RenderResult:
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


def get_roller(v: BaseModel, *args: Any, **kwargs: Any) -> RenderableType | None:
    rollable_type = Roller.Registry.get(type(v))

    if not rollable_type:
        return None

    rollable = rollable_type(v, *args, **kwargs)
    return rollable


class Roller:
    """Base class for all Rollers.

    Rollers can select from a choice of contained objects.


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


class OracleCollectionRoller(Roller):
    def __init__(
        self,
        collection: OracleTablesCollection
        | OracleTableSharedRolls
        | OracleTableSharedText
        | OracleTableSharedText2,
        *args: Any,
        **kwargs: Any,
    ):
        self.collection = collection
        self.args = args
        self.kwargs = kwargs

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        for v in self.collection.contents.values():
            yield OracleRoller(v, *self.args, **self.kwargs)


class CollectionRoller(Roller):
    def __init__(
        self,
        collection: NpcCollection | AssetCollection | AtlasCollection,
        *args: Any,
        **kwargs: Any,
    ):
        self.collection = collection
        self.args = args
        self.kwargs = kwargs

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        obj = random.choice(list(self.collection.contents.values()))
        yield get_renderable(obj, *self.args, **self.kwargs)


class OracleRoller(Roller):
    def __init__(
        self,
        oracle: EmbeddedOracleColumnText
        | EmbeddedOracleRollable
        | EmbeddedOracleTableText
        | OracleTableText
        | OracleTableText2
        | OracleTableText3
        | OracleColumnText
        | OracleColumnText2
        | OracleColumnText3,
        *_: Any,
        roll: int | None = None,
        **kwargs: Any,
    ):
        self.oracle = oracle
        self.dice = int(self.oracle.dice.split("d")[1])
        self.number_of_rolls = getattr(self.oracle, "number_of_rolls", 1)
        # self.args = args
        self.kwargs = kwargs

        if roll is not None:
            if roll < 1 or roll > int(self.dice):
                msg = f"Invalid roll: {roll} (Range d{self.dice})"
                raise ValueError(msg)
            self.roll = roll
        else:
            self.roll = random.randint(1, int(self.dice))

    def _oracle_rolls(self, oracle_rolls: list[OracleRoll]):
        for oracle_roll in oracle_rolls:
            number_of_rolls = getattr(oracle_roll, "number_of_rolls", 1)
            for n in range(number_of_rolls):
                try:
                    oracle = datasworn_tree.index[oracle_roll.oracle]
                    yield from OracleRoller(oracle)()
                except KeyError:
                    log.error(f"Unknown oracle: {oracle_roll.oracle} in {oracle_rolls}")

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        self.number_of_rolls, self.dice = self.oracle.dice.split("d")
        row = None
        for n in range(int(self.number_of_rolls)):
            for row in self.oracle.rows:
                if row.roll and row.roll.min <= self.roll <= row.roll.max:
                    # yield RollResult(roll=self.roll, obj=row, **self.kwargs)
                    yield get_renderable(
                        row, result=self.roll, expand=True, **self.kwargs
                    )


class TruthsRoller(Roller):
    def __init__(
        self,
        truths: list[Truth],
        *args,
        **kwargs,
    ):
        self.truths = truths

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        for truth in self.truths:
            yield TruthRoller(truth)


class TruthRoller(Roller):
    def __init__(
        self,
        truth: Truth,
        roll: int | None = None,
        **kwargs: Any,
    ):
        self.truth = truth
        self.kwargs = kwargs
        self.number_of_rolls, self.dice = self.truth.dice.split("d")

        if roll is not None:
            if roll < 1 or roll > int(self.dice):
                msg = f"Invalid roll: {roll} (Range d{self.dice})"
                raise ValueError(msg)
            self.roll = roll
        else:
            self.roll = random.randint(1, int(self.dice))

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        for option in self.truth.options:
            if option.roll and option.roll.min <= self.roll <= option.roll.max:
                yield get_renderable(option, **self.kwargs)

                if option.oracles:
                    for oracle in option.oracles.values():
                        yield get_roller(oracle)


class AssetRoller(Roller):
    def __init__(
        self,
        asset: Asset,
        roll: int | None = None,
        **kwargs: Any,
    ):
        self.asset = asset
        self.kwargs = kwargs

        na = len(self.asset.abilities)
        if roll is not None:
            if roll < 0 or roll > na:
                msg = f"Invalid roll: {roll} (Range {na})"
                raise ValueError(msg)
            self.roll = roll
        else:
            self.roll = random.randint(0, na)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        ability = self.asset.abilities[self.roll]
        yield get_renderable(ability, **self.kwargs)


class DelveSiteRoller(Roller):
    def __init__(
        self,
        delve_site: DelveSite,
        roll: int | None = None,
        **kwargs: Any,
    ):
        self.delve_site = delve_site
        self.kwargs = kwargs

        if roll is not None:
            if roll < 0 or roll > 100:
                msg = f"Invalid roll: {roll} (Range 100)"
                raise ValueError(msg)
            self.roll = roll
        else:
            self.roll = random.randint(0, 100)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        for denizen in self.delve_site.denizens:
            if denizen.roll and denizen.roll.min <= self.roll <= denizen.roll.max:
                yield get_renderable(denizen, **self.kwargs)


class MoveActionRollRoller(Roller):
    def __init__(
        self,
        move: MoveActionRoll,
        # roll: int | None = None,
        **kwargs: Any,
    ):
        self.move = move
        self.kwargs = kwargs

        # na = len(self.move.outcomes)
        # if roll is not None:
        #     if roll < 0 or roll > na:
        #         msg = f"Invalid roll: {roll} (Range {na})"
        #         raise ValueError(msg)
        #     self.roll = roll
        # else:
        self.roll = random.choice(["strong_hit", "weak_hit", "miss"])

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        outcome = getattr(self.move.outcomes, self.roll)
        yield get_renderable(outcome, **self.kwargs)


if __name__ == "__main__":
    from pysworn.common import datasworn_tree
    from rich.console import Console
    from rich.logging import RichHandler

    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    logging.getLogger("markdown_it").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)

    console = Console()
    console.print(Roller.Registry)

    datasworn_tree["starforged"]

    for k, v in datasworn_tree.index.items():
        if rollable := get_roller(v, plain=False):
            log.debug(f"'{k}': <{type(v).__name__}> -> <{type(rollable).__name__}>")
            # print(rollable)
