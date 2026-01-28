import logging
import random
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
    Asset,
    AssetAbility,
    AssetCollection,
    AtlasCollection,
    AtlasEntry,
    BaseModel,
    ChallengeRank,
    DelveSite,
    DelveSiteDenizen,
    DelveSiteDomain,
    DelveSiteDomainDanger,
    DelveSiteDomainFeature,
    DelveSiteTheme,
    DelveSiteThemeDanger,
    DelveSiteThemeFeature,
    EmbeddedActionRollMove,
    EmbeddedMove,
    EmbeddedOracleColumnText,
    EmbeddedOracleRollable,
    EmbeddedOracleTableText,
    EmbeddedSpecialTrackMove,
    Expansion,
    MoveActionRoll,
    MoveCategory,
    MoveNoRoll,
    MoveOutcome,
    MoveProgressRoll,
    MoveSpecialTrack,
    Npc,
    NpcCollection,
    NpcVariant,
    OracleColumnText,
    OracleColumnText2,
    OracleColumnText3,
    OracleRoll,
    OracleRollable,
    OracleRollableRowText,
    OracleRollableRowText2,
    OracleRollableRowText3,
    OracleTablesCollection,
    OracleTableSharedRolls,
    OracleTableSharedText,
    OracleTableSharedText2,
    OracleTableText,
    OracleTableText2,
    OracleTableText3,
    Rarity,
    Rules,
    Ruleset,
    TriggerActionRollCondition,
    TriggerProgressRollCondition,
    TriggerSpecialTrackCondition,
    Truth,
    TruthOption,
)
from rich import print

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def get_rollable(v: BaseModel):
    rollable_type = PyswornRoll.Registry.get(type(v))

    if rollable_type:
        rollable = rollable_type(v)
        return rollable

    return None


class PyswornRoll:
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
            if v in PyswornRoll.Registry:
                raise KeyError(f"Duplicate renderable type: {v}")
            if v.__module__ == "datasworn.core.models":
                PyswornRoll.Registry[v] = cls
                log.debug(f"{v}: {cls}")

    def __init__(self, obj: BaseModel):
        self.obj = obj

    # def __iter__(self):
    #     return self

    # def __next__(self):
    #     log.error("cannot roll")
    #     raise StopIteration


class PyswornCollectionRoll(PyswornRoll):
    def __init__(
        self,
        collection: OracleTablesCollection
        | OracleTableSharedRolls
        | OracleTableSharedText
        | OracleTableSharedText2,
    ):
        self.collection = collection

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        for v in self.collection.contents.values():
            yield from PyswornOracleRoll(v)()


class PyswornOracleRoll(PyswornRoll):
    def __init__(
        self,
        oracle: OracleTableText
        | OracleTableText2
        | OracleTableText3
        | OracleColumnText
        | OracleColumnText2
        | OracleColumnText3,
    ):
        self.oracle = oracle
        self.dice = int(self.oracle.dice.split("d")[1])

    def _oracle_rolls(self, oracle_rolls: list[OracleRoll]):
        for oracle_roll in oracle_rolls:
            number_of_rolls = getattr(oracle_roll, "number_of_rolls", 1)
            for n in range(number_of_rolls):
                try:
                    oracle = datasworn_tree.index[oracle_roll.oracle]
                    yield from PyswornOracleRoll(oracle)()
                except KeyError:
                    yield oracle_roll

    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        number_of_rolls = getattr(self.oracle, "number_of_rolls", 1)
        for n in range(number_of_rolls):
            roll = random.randint(1, self.dice)
            for row in self.oracle.rows:
                if row.roll and row.roll.min <= roll <= row.roll.max:
                    if oracle_rolls := row.oracle_rolls:
                        yield from self._oracle_rolls(oracle_rolls)
                    else:
                        yield f"{n} [dim]{self.oracle.name}[/] {roll}: {row.text}"


# class OracleRollable
if __name__ == "__main__":
    from pysworn.common import datasworn_tree
    from rich import print

    print(PyswornRoll.Registry)

    for k in datasworn_tree:
        datasworn_tree[k]

    for k, v in datasworn_tree.index.items():
        if rollable := get_rollable(v):
            # print(f"'{k}'")
            # roll, r = rollable()

            for r in rollable():
                roll = 0
                print(f"{getattr(r, 'text', r)}")
