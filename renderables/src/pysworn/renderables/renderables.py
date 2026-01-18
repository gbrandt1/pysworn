import logging
import random
import re
from inspect import getfullargspec
from typing import Any, TypeAliasType, Union, get_args, get_origin

from datasworn.core import datasworn_tree
from datasworn.core.models import (
    Asset,
    AssetAbility,
    AssetCollection,
    AtlasCollection,
    AtlasEntry,
    BaseModel,
    DelveSite,
    DelveSiteDenizen,
    DelveSiteDomain,
    DelveSiteDomainDanger,
    DelveSiteDomainFeature,
    DelveSiteTheme,
    DelveSiteThemeDanger,
    DelveSiteThemeFeature,
    EmbeddedMove,
    EmbeddedOracleColumnText,
    EmbeddedOracleTableText,
    Expansion,
    Move,
    MoveCategory,
    Npc,
    NpcCollection,
    NpcVariant,
    OracleColumnText,
    OracleColumnText2,
    OracleColumnText3,
    OracleRollable,
    OracleRollableRow,
    OracleTablesCollection,
    OracleTableSharedRolls,
    OracleTableSharedText,
    OracleTableSharedText2,
    OracleTableText,
    OracleTableText2,
    OracleTableText3,
    Rarity,
    Ruleset,
    Truth,
    TruthOption,
)
from rich.columns import Columns
from rich.console import Console, ConsoleOptions, Group, RenderableType, RenderResult
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


RENDERABLE_TYPES: dict[type, type] = {}

log.debug("Loading Renderables")

# datasworn_tree = DataswornTree()
index = datasworn_tree.index


def breadcrumbs(id_: str) -> RenderableType:
    if ":" not in id_:
        return index[id_].name.upper()
    *path, last = id_.split(":")[1].upper().replace("_", " ").split("/")
    return Group(
        Markdown(" -> ".join([p for p in path] + [f"**{last}**\n\n"])),
        Rule(style="dim white"),
    )


def get_renderable(obj: BaseModel, *args: Any, **kwargs: Any) -> RenderableType | None:
    # from rich.pretty import Pretty

    # obj = index[id_]
    # rule_type = id_.split(":")[0]
    # renderable = RENDERABLE_KEYS.get(rule_type)
    # if not renderable:
    #     return Pretty(obj, max_depth=2, expand_all=True)
    # return renderable(obj)

    # def get_renderable(self) -> RenderableType:
    # obj = datasworn_tree.index.get(self.id_)
    r_type = type(obj)
    if r_type in RENDERABLE_TYPES:
        renderable = RENDERABLE_TYPES.get(r_type)
    elif r_type.__mro__[1] in RENDERABLE_TYPES:
        renderable = RENDERABLE_TYPES.get(r_type.__mro__[1])
    else:
        renderable = None
    # group: list[RenderableType | str] = [f"{obj.id} {type(obj).__mro__}"]
    if renderable:
        # group.append(Panel(renderable(obj, *args, **kwargs)))
        return Panel(renderable(obj, *args, **kwargs))
    # return Group(*group)
    return None


class PyswornRenderable:
    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)

        fullargspec = getfullargspec(cls.__init__)
        # log.debug(f"{cls}: {fullargspec}")
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
            if v in RENDERABLE_TYPES:
                raise KeyError(f"Duplicate renderable type: {v}")
            RENDERABLE_TYPES[v] = cls
            log.debug(f"{v}: {cls}")
            # parent = v.__mro__[1]
            # if parent is not BaseModel:
            #     RENDERABLE_TYPES[parent] = cls


class RuleSetRenderable(PyswornRenderable):
    def __init__(self, ruleset: Ruleset | Expansion, *args, **kwargs):
        self.ruleset = ruleset

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        msg = f"# {self.ruleset.title}\n\n"
        msg += "by "
        for author in self.ruleset.authors:
            msg += f"{author.name} "
            if author.email:
                msg += f"{author.email} "
            if author.url:
                msg += f"{author.url} "
        msg += "\n\n"
        msg += f"[{self.ruleset.url}]({self.ruleset.url}) - "
        msg += f"Licensed for our use under {self.ruleset.license}\n\n"
        yield Markdown(msg)


class CategoryRenderable(PyswornRenderable):
    def __init__(self, category: dict, *args, **kwargs):
        self.category = category

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        msg = ", ".join([f"[{k.title()}]({v.id})" for k, v in self.category.items()])

        yield Markdown(msg)


class CollectionRenderable:
    def __init__(self, collection: BaseModel, *args, **kwargs):
        self.collection = collection

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        msg = f"## {self.collection.name}\n\n"
        if self.collection.summary:
            msg += f"{self.collection.summary}\n\n"

        msg += (
            "Entries: "
            + ", ".join(
                [f"[{v.name}]({v.id})" for v in self.collection.contents.values()]
            )
            + "\n\n"
        )
        collections = []
        if hasattr(self.collection, "collections") and self.collection.collections:
            # if self.collection.collections:
            for collection in self.collection.collections.values():
                collections.append(CollectionRenderable(collection))
        if len(collections) == 0:
            yield Markdown(msg)
        else:
            yield Group(
                Markdown(msg),
                Panel(
                    Group(*collections),
                    border_style="dim",
                ),
            )


class AtlasCollectionRenderable(PyswornRenderable, CollectionRenderable):
    def __init__(self, collection: AtlasCollection):
        self.collection = collection


class MoveCategoryRenderable(PyswornRenderable, CollectionRenderable):
    def __init__(self, collection: MoveCategory):
        self.collection = collection


class AssetCollectionRenderable(PyswornRenderable, CollectionRenderable):
    def __init__(self, collection: AssetCollection):
        self.collection = collection


class AtlasEntryRenderable(PyswornRenderable):
    def __init__(self, atlas_entry: AtlasEntry, *args, **kwargs):
        self.atlas_entry = atlas_entry

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.atlas_entry.id)
        if self.atlas_entry.summary:
            yield Markdown(self.atlas_entry.summary)


class AssetAbilityRenderable(PyswornRenderable):
    def __init__(self, ability: AssetAbility):
        self.ability = ability

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        from rich.table import Table

        t = Table.grid(padding=(0, 1), pad_edge=False)
        t.add_row(
            "⬤" if self.ability.enabled else "◯", Markdown(f"{self.ability.text}")
        )
        moves = []
        # for move in self.ability.moves:
        #     moves.append(MoveRenderable(move))
        yield Group(t, *moves)


class AssetRenderable(PyswornRenderable):
    def __init__(self, asset: Asset):
        self.asset = asset

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.asset.id)
        for ability in self.asset.abilities:
            yield AssetAbilityRenderable(ability)


class DelveSiteRenderable(PyswornRenderable):
    def __init__(self, delve_site: DelveSite):
        self.delve_site = delve_site

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.delve_site.id)
        # msg = f"{self.delve_site.category.upper()} \n{self.delve_site.name.upper()}\n"
        theme = index[self.delve_site.theme].name
        domain = index[self.delve_site.domain].name
        region = index[self.delve_site.region].name
        msg = f"{theme} {domain} in the {region}. "
        msg += f"Rank: {self.delve_site.rank}\n\n"
        # denizens = ["| Roll | Frequency | NPC | Name |\n| --- | --- | --- | --- |\n"]
        denizens = "Denizens\n\nRoll | Frequency | NPC | Name\n---|---|---|---\n"
        for denizen in self.delve_site.denizens:
            denizens += str(DelveSiteDenizenRenderable(denizen))
        yield Markdown(denizens)


class DelveSiteDenizenRenderable(PyswornRenderable):
    def __init__(self, denizen: DelveSiteDenizen):
        self.denizen = denizen

    def __str__(self):
        roll = f"{self.denizen.roll.min}-{self.denizen.roll.max} "
        msg = f"{roll:^7} "
        msg += f"| {self.denizen.frequency} "
        if self.denizen.npc:
            npc = index[self.denizen.npc].name
            msg += f"| {npc} "
        if self.denizen.name:
            msg += f"| {self.denizen.name} "

        return msg + "\n"

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Markdown(str(self))


class DelveSiteThemeRenderable(PyswornRenderable):
    def __init__(self, theme: DelveSiteTheme):
        self.theme = theme

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.theme.id)
        dangers: list[RenderableType] = [Markdown("## Dangers\n\n")]
        for danger in self.theme.dangers:
            dangers.append(DelveSiteFeatureRenderable(danger))
        features: list[RenderableType] = [Markdown("## Features\n\n")]
        for feature in self.theme.features:
            features.append(DelveSiteFeatureRenderable(feature))
        yield Group(*dangers, *features)


class DelveSiteDomainRenderable(PyswornRenderable):
    def __init__(self, domain: DelveSiteDomain):
        self.domain = domain

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.domain.id)
        dangers: list[RenderableType] = [Markdown("## Dangers\n\n")]
        for danger in self.domain.dangers:
            dangers.append(DelveSiteFeatureRenderable(danger))
        features: list[RenderableType] = [Markdown("## Features\n\n")]
        for feature in self.domain.features:
            features.append(DelveSiteFeatureRenderable(feature))
        yield Group(*dangers, *features)


class DelveSiteFeatureRenderable(PyswornRenderable):
    def __init__(
        self,
        feature: DelveSiteDomainFeature
        | DelveSiteThemeFeature
        | DelveSiteDomainDanger
        | DelveSiteThemeDanger,
    ):
        self.feature = feature

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        msg = f"{self.feature.roll.min}-{self.feature.roll.max}: {self.feature.text} "
        yield Markdown(msg)


class MoveRenderable(PyswornRenderable):
    def __init__(
        self,
        move: Move | EmbeddedMove,
        *,
        outcome: str | None = None,
        **kwargs,
    ):
        self.move = move
        self.outcome = outcome

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.move.id)
        if not self.outcome:
            yield Markdown(self.move.text)
        else:
            yield Markdown(getattr(self.move.outcomes, self.outcome).text)


class NpcVariantRenderable(PyswornRenderable):
    def __init__(self, npc: NpcVariant):
        self.npc = npc

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        msg = f"**{self.npc.name}** {self.npc.nature} Rank {self.npc.rank}\n\n"
        for attr in ("drives", "features", "tactics"):
            if hasattr(self.npc, attr) and getattr(self.npc, attr):
                msg += f"### {attr.title()}\n\n"
                for item in getattr(self.npc, attr):
                    msg += f"- {item}\n"

        if self.npc.summary:
            msg += f"{self.npc.summary}\n\n"
        if hasattr(self.npc, "description") and self.npc.description:
            msg += f"{self.npc.description}\n\n"
        if hasattr(self.npc, "quest_starter") and self.npc.quest_starter:
            msg += f"> *{self.npc.quest_starter}*\n\n"

        yield Markdown(msg)


class NpcRenderable(PyswornRenderable):
    def __init__(self, npc: Npc):
        self.npc = npc

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        msg = breadcrumbs(self.npc.id)
        variants = [NpcVariantRenderable(self.npc)]
        for variant in self.npc.variants.values():
            variants.append(NpcVariantRenderable(variant))
        yield Group(Markdown(msg), *variants)


class NpcCollectionRenderable(PyswornRenderable, CollectionRenderable):
    def __init__(self, collection: NpcCollection):
        self.collection = collection


class OracleTablesCollectionRenderable(PyswornRenderable):
    def __init__(
        self,
        collection: OracleTablesCollection,
        # | OracleTableSharedText
        # | OracleTableSharedText2,
        *,
        roll=str | None,
    ):
        self.collection = collection
        self.roll = roll

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.collection.id)
        # f"## {self.collection.name}\n\n"
        if self.collection.summary:
            yield Markdown(f"{self.collection.summary}\n")

        if self.roll is not None:
            for oracle in self.collection.contents.values():
                yield OracleRollableRenderable(oracle, roll="")
            return

        yield Markdown(
            "Oracles: "
            + ", ".join(
                [f"[{v.name}]({v.id})" for v in self.collection.contents.values()]
            )
            + "\n\n"
        )
        collections = []
        if hasattr(self.collection, "collections") and self.collection.collections:
            for collection in self.collection.collections.values():
                collections.append(OracleTablesCollectionRenderable(collection))
        if len(collections) > 0:
            yield Panel(
                Group(*collections),
                border_style="dim",
            )


class OracleTablesSharedRenderable(PyswornRenderable):
    def __init__(
        self,
        collection: OracleTableSharedRolls
        | OracleTableSharedText
        | OracleTableSharedText2,
        *,
        roll=None,
    ):
        self.collection = collection
        self.roll = roll

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        msg = f"## {self.collection.name}\n\n"
        if self.collection.summary:
            msg += f"{self.collection.summary}\n\n"

        msg += (
            "Oracles: "
            + ", ".join(
                [f"[{v.name}]({v.id})" for v in self.collection.contents.values()]
            )
            + "\n\n"
        )
        collections = []
        if hasattr(self.collection, "collections") and self.collection.collections:
            for collection in self.collection.collections.values():
                collections.append(CollectionRenderable(collection))
        if len(collections) == 0:
            yield Markdown(msg)
        else:
            yield Group(
                Markdown(msg),
                Panel(
                    Group(*collections),
                    border_style="dim",
                ),
            )


class OracleRollableRenderable(PyswornRenderable):
    def __init__(
        self,
        table: OracleRollable
        | OracleTableText
        | OracleTableText2
        | OracleTableText3
        | OracleColumnText
        | OracleColumnText2
        | OracleColumnText3
        | EmbeddedOracleColumnText
        | EmbeddedOracleTableText,
        *,
        roll=None,
    ):
        self.table = table

        if roll is None:
            self.rows = [OracleRollableRowRenderable(row) for row in self.table.rows]
            return

        if len(roll) > 0:
            self.roll = int(roll)
        if roll == "":
            self.roll = random.randint(1, int(self.table.dice.split("d")[1]))

        for row in self.table.rows:
            if row.roll and row.roll.min <= self.roll <= row.roll.max:
                self.rows = [OracleRollableRowRenderable(row)]
                break
        # row = random.choice(self.table.rows)
        self.rows = [OracleRollableRowRenderable(row)]

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.table.id)
        yield Columns(
            [str(row) for row in self.rows],
            expand=True,
            equal=True,
            column_first=True,
        )


class OracleRollableRowRenderable(PyswornRenderable):
    def __init__(self, row: OracleRollableRow):
        self.row = row

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Text.from_markup(str(self))

    def __str__(self):
        roll = self.row.roll
        rtxt = ""
        if roll:
            roll_min = self.row.roll.min if self.row.roll.min else ""
            roll_max = self.row.roll.max if self.row.roll.max else ""
            if roll_min == roll_max:
                rtxt = f"{roll_min:^8}"
            else:
                rtxt = f"{roll_min}-{roll_max}"

        text = self.row.text
        text = re.sub(r"\[(.+?)\]\(.+?\)", (r"\1").upper(), text)

        msg = f"{rtxt:^8} {text}"
        # msg = f"{rtxt:^7} [link={self.row.id}]{text}[/link]"

        # if hasattr(self.row, "text2") and self.row.text2:
        #     msg += f" {self.row.text2}"
        # if hasattr(self.row, "text3") and self.row.text3:
        #     msg += f" {self.row.text3}"
        return msg


class RarityRenderable(PyswornRenderable):
    def __init__(self, rarity: Rarity):
        self.rarity = rarity

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        asset = index[self.rarity.asset]
        yield breadcrumbs(self.rarity.id)
        yield f"for {asset.name.upper()} (XP cost: {self.rarity.xp_cost})"
        if hasattr(self.rarity, "description") and self.rarity.description:
            yield f"{self.rarity.description}\n\n"


class TruthOptionRenderable(PyswornRenderable):
    def __init__(self, truth: TruthOption):
        self.truth = truth

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        msg = ""
        roll = self.truth.roll
        msg += f"**{roll.min}-{roll.max}** "
        if self.truth.summary:
            msg += f"**{self.truth.summary}**\n\n"
        # msg += f"{self.truth.description}\n\n"
        oracles = []
        for oracle in self.truth.oracles.values():
            oracles.append(OracleRollableRenderable(oracle))
        msg2 = f"\n> *{self.truth.quest_starter}*\n\n"
        yield Group(Markdown(msg), *oracles, Markdown(msg2))


class TruthRenderable(PyswornRenderable):
    def __init__(self, truth: Truth):
        self.truth = truth

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        name = f"# {self.truth.name}"
        your_character = ""
        if hasattr(self.truth, "your_character") and self.truth.your_character:
            your_character = f"> *{self.truth.your_character}*\n\n"
        options = []
        for option in self.truth.options:
            options.append(TruthOptionRenderable(option))
            options.append(Rule(style="dim white"))
        yield Group(Markdown(name), *options, Markdown(your_character))


class RulesRenderable(PyswornRenderable):
    def __init__(self, rules):
        self.rules = rules

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        attrs = (
            "condition_meters",
            "impacts",
            "special_tracks",
            "stats",
            "tags",
        )
        rules = []
        for attr in attrs:
            if hasattr(self.rules, attr) and (obj := getattr(self.rules, attr)):
                rules.append(Markdown(f"## {attr}"))
                for k, v in obj.items():
                    if attr == "tags":
                        rules.append(Markdown(f"### {k}"))
                    else:
                        rules.append(Markdown(f"### {v.label}"))
                    rules.append(Markdown(v.description))
                    # rules.append(Pretty(v))
        yield Group(*rules)
