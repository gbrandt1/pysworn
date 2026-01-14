import logging
import re
from inspect import getfullargspec
from typing import Any, TypeAliasType, Union, get_args, get_origin

from datasworn.core import index
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
    Move,
    MoveCategory,
    Npc,
    NpcCollection,
    NpcVariant,
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


def breadcrumbs(id_: str) -> str:
    return index[id_].name


RENDERABLE_TYPES: dict[type, type] = {}

log.debug("Loading Renderables")


class Selfregistering:
    RENDERABLE_TYPES: dict[str, type] = {}

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


class RuleSetRenderable(Selfregistering):
    def __init__(self, ruleset: Ruleset):
        self.ruleset = ruleset

    def __rich__(self):
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
        return Markdown(msg)


class CategoryRenderable(Selfregistering):
    def __init__(self, category: dict[str, BaseModel]):
        self.category = category

    def __rich__(self):
        msg = ", ".join([f"[{k.title()}]({v.id})" for k, v in self.category.items()])

        return Markdown(msg)


class CollectionRenderable:
    def __rich__(self):
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
        if self.collection.collections:
            for collection in self.collection.collections.values():
                collections.append(CollectionRenderable[TCollection](collection))
        if len(collections) == 0:
            return Markdown(msg)
        else:
            return Group(
                Markdown(msg),
                Panel(
                    Group(*collections),
                    border_style="dim",
                ),
            )


class AtlasCollectionRenderable(Selfregistering, CollectionRenderable):
    def __init__(self, collection: AtlasCollection):
        self.collection = collection


class MoveCategoryRenderable(Selfregistering, CollectionRenderable):
    def __init__(self, collection: MoveCategory):
        self.collection = collection


class AssetCollectionRenderable(Selfregistering, CollectionRenderable):
    def __init__(self, collection: AssetCollection):
        self.collection = collection


class AtlasEntryRenderable(Selfregistering):
    def __init__(self, atlas_entry: AtlasEntry):
        self.atlas_entry = atlas_entry

    def __rich__(self):
        msg = f"## {self.atlas_entry.name}\n\n"
        msg += f"{self.atlas_entry.summary}\n\n"
        # msg += f"{self.atlas_entry.description}\n\n"
        return Markdown(msg)


class AssetAbilityRenderable(Selfregistering):
    def __init__(self, ability: AssetAbility):
        self.ability = ability

    def __rich__(self):
        from rich.table import Table

        t = Table.grid(padding=(0, 1), pad_edge=False)
        t.add_row(
            "⬤" if self.ability.enabled else "◯", Markdown(f"{self.ability.text}")
        )
        moves = []
        # for move in self.ability.moves:
        #     moves.append(MoveRenderable(move))
        return Group(t, *moves)


class AssetRenderable(Selfregistering):
    def __init__(self, asset: Asset):
        self.asset = asset

    def __rich__(self):
        msg = breadcrumbs(self.asset.id)
        # msg = f"{self.asset.category.upper()} \n{self.asset.name.upper()}"
        abilities = []
        for ability in self.asset.abilities:
            abilities.append("\n")
            abilities.append(AssetAbilityRenderable(ability))
        return Group(Markdown(msg), *abilities)


class DelveSiteRenderable(Selfregistering):
    def __init__(self, delve_site: DelveSite):
        self.delve_site = delve_site

    def __rich__(self):
        msg = breadcrumbs(self.delve_site.id)
        # msg = f"{self.delve_site.category.upper()} \n{self.delve_site.name.upper()}\n"
        theme = index[self.delve_site.theme].name
        domain = index[self.delve_site.domain].name
        region = index[self.delve_site.region].name
        msg += f"{theme} {domain} in the {region}. "
        msg += f"Rank: {self.delve_site.rank}\n\n"
        # denizens = ["| Roll | Frequency | NPC | Name |\n| --- | --- | --- | --- |\n"]
        denizens = "Denizens\n\nRoll | Frequency | NPC | Name\n---|---|---|---\n"
        for denizen in self.delve_site.denizens:
            denizens += str(DelveSiteDenizenRenderable(denizen))
        return Group(Markdown(msg), Rule(style="dim white"), Markdown(denizens))


class DelveSiteDenizenRenderable(Selfregistering):
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

    def __rich__(self):
        return Markdown(str(self))


class DelveSiteThemeRenderable(Selfregistering):
    def __init__(self, theme: DelveSiteTheme):
        self.theme = theme

    def __rich__(self):
        msg = breadcrumbs(self.theme.id)
        # msg = f"{self.theme.category.upper()} \n{self.theme.name.upper()}\n"
        dangers: list[RenderableType] = [Markdown("## Dangers\n\n")]
        for danger in self.theme.dangers:
            dangers.append(DelveSiteFeatureRenderable(danger))
        features: list[RenderableType] = [Markdown("## Features\n\n")]
        for feature in self.theme.features:
            features.append(DelveSiteFeatureRenderable(feature))
        return Group(Markdown(msg), *dangers, *features)  # Markdown(msg)


class DelveSiteDomainRenderable(Selfregistering):
    def __init__(self, domain: DelveSiteDomain):
        self.domain = domain

    def __rich__(self):
        msg = breadcrumbs(self.domain.id)
        # msg = f"{self.domain.category.upper()} \n{self.domain.name.upper()}\n"
        dangers: list[RenderableType] = [Markdown("## Dangers\n\n")]
        for danger in self.domain.dangers:
            dangers.append(DelveSiteFeatureRenderable(danger))
        features: list[RenderableType] = [Markdown("## Features\n\n")]
        for feature in self.domain.features:
            features.append(DelveSiteFeatureRenderable(feature))
        return Group(Markdown(msg), *dangers, *features)


class DelveSiteFeatureRenderable(Selfregistering):
    def __init__(
        self,
        feature: DelveSiteDomainFeature
        | DelveSiteThemeFeature
        | DelveSiteDomainDanger
        | DelveSiteThemeDanger,
    ):
        self.feature = feature

    def __rich__(self):
        msg = f"{self.feature.roll.min}-{self.feature.roll.max}: {self.feature.text} "
        return Markdown(msg)
        # return Pretty(self.feature)


class MoveRenderable(Selfregistering):
    def __init__(self, move: Move | EmbeddedMove):
        self.move = move

    def __rich__(self):
        msg = (
            # f"{self.move.category.upper()}\n"
            f"{self.move.name.upper()}\n\n{self.move.text}"
        )
        return Markdown(msg)


class NpcVariantRenderable(Selfregistering):
    def __init__(self, npc: NpcVariant):
        self.npc = npc

    def __rich__(self):
        msg = f"**{self.npc.name}** {self.npc.nature} Rank {self.npc.rank}\n\n"
        for attr in ("drives", "features", "tactics"):
            if hasattr(self.npc, attr) and getattr(self.npc, attr):
                msg += f"### {attr.title()}\n\n"
                for item in getattr(self.npc, attr):
                    msg += f"- {item}\n"

        if self.npc.summary:
            msg += f"{self.npc.summary}\n\n"
        msg += f"{self.npc.description}\n\n"
        if hasattr(self.npc, "quest_starter") and self.npc.quest_starter:
            msg += f"> *{self.npc.quest_starter}*\n\n"

        return Markdown(msg)


class NpcRenderable(Selfregistering):
    def __init__(self, npc: Npc):
        self.npc = npc

    def __rich__(self):
        msg = breadcrumbs(self.npc.id)
        variants = [NpcVariantRenderable(self.npc)]
        for variant in self.npc.variants.values():
            variants.append(NpcVariantRenderable(variant))
        return Group(Markdown(msg), *variants)


class NpcCollectionRenderable(Selfregistering, CollectionRenderable):
    def __init__(self, collection: NpcCollection):
        self.collection = collection


class OracleTablesCollectionRenderable(Selfregistering):
    def __init__(
        self,
        collection: OracleTablesCollection,
        # | OracleTableSharedText
        # | OracleTableSharedText2,
    ):
        self.collection = collection

    def __rich__(self):
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
                collections.append(OracleTablesCollectionRenderable(collection))
        if len(collections) == 0:
            return Markdown(msg)
        else:
            return Group(
                Markdown(msg),
                Panel(
                    Group(*collections),
                    border_style="dim",
                ),
            )


class OracleTablesSharedRenderable(Selfregistering):
    def __init__(
        self,
        collection: OracleTableSharedRolls
        | OracleTableSharedText
        | OracleTableSharedText2,
    ):
        self.collection = collection

    def __rich__(self):
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
            return Markdown(msg)
        else:
            return Group(
                Markdown(msg),
                Panel(
                    Group(*collections),
                    border_style="dim",
                ),
            )


class OracleRollableRenderable(Selfregistering):
    def __init__(
        self,
        table: OracleRollable
        | OracleTableText
        | OracleTableText2
        | OracleTableText3
        | EmbeddedOracleColumnText
        | EmbeddedOracleTableText,
    ):
        self.table = table
        self.rows = [OracleRollableRowRenderable(row) for row in self.table.rows]

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        msg = breadcrumbs(self.table.id)
        if msg:
            yield Text.from_markup(msg)
        yield Rule(style="dim white")
        yield Columns(
            self.rows,
            expand=True,
            equal=True,
            column_first=True,
        )


class OracleRollableRowRenderable(Selfregistering):
    def __init__(self, row: OracleRollableRow):
        self.row = row

    def __rich__(self):
        return Text.from_markup(str(self))
        # return Markdown(str(self))

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


class RarityRenderable(Selfregistering):
    def __init__(self, rarity: Rarity):
        self.rarity = rarity

    def __rich__(self):
        asset = index[self.rarity.asset]
        msg = (
            f"**{self.rarity.name}** "
            # f"[{asset.name}]({self.rarity.asset})"
            f"for {asset.name.upper()} "
            f"(XP cost: {self.rarity.xp_cost})\n\n"
            f"---\n\n"
            f"{self.rarity.description}\n\n"
        )
        return Markdown(msg)


class TruthOptionRenderable(Selfregistering):
    def __init__(self, truth: TruthOption):
        self.truth = truth

    def __rich__(self):
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
        return Group(Markdown(msg), *oracles, Markdown(msg2))


class TruthRenderable(Selfregistering):
    def __init__(self, truth: Truth):
        self.truth = truth

    def __rich__(self):
        name = f"# {self.truth.name}"
        your_character = ""
        if hasattr(self.truth, "your_character") and self.truth.your_character:
            your_character = f"> *{self.truth.your_character}*\n\n"
        options = []
        for option in self.truth.options:
            options.append(TruthOptionRenderable(option))
            options.append(Rule(style="dim white"))
        return Group(Markdown(name), *options, Markdown(your_character))


class RulesRenderable(Selfregistering):
    def __init__(self, rules):
        self.rules = rules

    def __rich__(self):
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
        return Group(*rules)
