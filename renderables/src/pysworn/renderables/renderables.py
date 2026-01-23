import logging
import random
import re
from inspect import getfullargspec
from itertools import cycle
from typing import Any, ClassVar, TypeAliasType, Union, get_args, get_origin

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
    EmbeddedMove,
    EmbeddedOracleColumnText,
    EmbeddedOracleRollable,
    EmbeddedOracleTableText,
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
    OracleRollable,
    OracleRollableRow,
    OracleRollableRowText,
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
    Truth,
    TruthOption,
)
from pysworn.common import datasworn_tree
from rich.columns import Columns
from rich.console import (
    Console,
    ConsoleOptions,
    ConsoleRenderable,
    Group,
    RenderableType,
    RenderResult,
)
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

# from datasworn.src.pysworn.datasworn._datasworn import TaggableNodeType

RENDERABLE_TYPES: dict[type, type] = {}

CHALLENGE_RANK = {
    ChallengeRank.int_1: "troublesome",
    ChallengeRank.int_2: "dangerous",
    ChallengeRank.int_3: "formidable",
    ChallengeRank.int_4: "extreme",
    ChallengeRank.int_5: "epic",
}

log = logging.getLogger(__name__)

index = datasworn_tree.index


# Helper Functions


def name_or_id(id_: str | None) -> str:
    if not id_:
        return ""
    if obj := index.get(id_, None):
        if name := getattr(obj, "canonical_name", None):
            name.replace("Cursed", "🕱 Cursed")
            return name
        if name := getattr(obj, "name", None):
            name.replace("Cursed", "🕱 Cursed")
            return name
    return f"*{id_.split('/')[-1].title().replace('_', ' ')}*"


def breadcrumbs(id_: str) -> RenderableType:
    if ":" not in id_:
        return index[id_].name
    *path, last = id_.split(":")[1].title().replace("_", " ").split("/")
    return Group(
        # Markdown(" -> ".join([p for p in path])),  # + [f"**{last}**\n\n"])),
        # Rule(style="dim white"),
        Text.from_markup(f"[b]{name_or_id(id_).upper()}[/]"),
        "",
    )


def _render_text_with_embeds(
    text: str,
    id_: str | None = None,
):
    text_ = re.sub(r"{{.*?}}", "", text)
    yield Markdown(text_)

    oracles_ids = re.findall(r"{{(.*?)}}", text)
    for oracle_id in oracles_ids:
        id_embed = oracle_id.split(">")[1]
        if id_embed == id_:
            yield Markdown(f"- **{oracle_id}**", style="red")
        elif id_embed not in index:
            yield Markdown(f"- **{oracle_id}**", style="red")
        #     yield Markdown(f"- {oracle_id}")
        # elif oracle := index[id_]:
        else:
            yield Panel(get_renderable(index[id_embed]))
        # else:
        #     yield Markdown(f"- Oracle {oracle_id} not found")


def get_renderable(obj: BaseModel, *args: Any, **kwargs: Any) -> RenderableType | str:
    r_type = type(obj)
    renderable = RENDERABLE_TYPES.get(r_type, None)
    if renderable:
        # return Panel(renderable(obj, *args, **kwargs))
        if source := getattr(obj, "source", None):
            return Panel(
                renderable(obj, *args, **kwargs),
                title=renderable.BORDER_TITLE.upper(),
                title_align="left",
                subtitle=f"[{source.title}, {source.page}]",
                subtitle_align="right",
                border_style="dim",
                # width=80,
            )
        else:
            return renderable(obj, *args, **kwargs)
    return f"No renderable found for {type(obj)} ({getattr(obj, 'id', None)})"


class PyswornRenderable(ConsoleRenderable):
    BORDER_TITLE: ClassVar[str | None] = None
    MAX_WIDTH: ClassVar[int | None] = None

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)

        fullargspec = getfullargspec(cls.__init__)
        for k, v in fullargspec.annotations.items():
            log.debug(f"{k}: {v.__class__} {v}")
            cls._resolve_type(v)

        if not cls.BORDER_TITLE:
            cls.BORDER_TITLE = cls.__name__.replace("Renderable", "")

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
            if v.__module__ == "datasworn.core.models":
                RENDERABLE_TYPES[v] = cls
                log.debug(f"{v}: {cls}")

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield "[red]no renderable implemented[/]"


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
        yield breadcrumbs(self.collection.id)
        # yield Markdown(f"**{self.collection.name.upper()}**")

        if summary := getattr(self.collection, "summary", None):
            yield Markdown(f"**{summary}**")
            yield ""

        if contents := getattr(self.collection, "contents", None):
            yield "[cyan]" + " ".join(contents) + "[/]"

        if collections := getattr(self.collection, "collections", None):
            for collection in self.collection.collections.values():
                collections.append(CollectionRenderable(collection))
            yield Group(
                Panel(
                    Group(*collections),
                    border_style="dim",
                ),
            )


class AtlasCollectionRenderable(CollectionRenderable, PyswornRenderable):
    BORDER_TITLE = "Atlas"

    def __init__(self, collection: AtlasCollection):
        self.collection = collection


class AtlasEntryRenderable(PyswornRenderable):
    BORDER_TITLE = "Atlas Entry"

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


class AssetCollectionRenderable(CollectionRenderable, PyswornRenderable):
    BORDER_TITLE = "Asset Type"

    def __init__(self, collection: AssetCollection):
        self.collection = collection


class DelveSiteRenderable(PyswornRenderable):
    BORDER_TITLE = "Site"

    def __init__(self, delve_site: DelveSite):
        self.delve_site = delve_site

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.delve_site.id)
        yield Markdown(f"**Rank:** {CHALLENGE_RANK[self.delve_site.rank].title()}")
        yield Markdown(f"**Theme:** {name_or_id(self.delve_site.theme)}")
        yield Markdown(f"**Domain:** {name_or_id(self.delve_site.domain)}")
        yield Markdown(f"Region: {name_or_id(self.delve_site.region)}")
        yield ""

        yield Markdown(self.delve_site.description)
        # denizens = ["| Roll | Frequency | NPC | Name |\n| --- | --- | --- | --- |\n"]
        denizens = "Roll | Frequency | NPC | Name\n---|---|---|---\n"
        for denizen in self.delve_site.denizens:
            denizens += DelveSiteDenizenRenderable(denizen)._render()
        yield Markdown(denizens)


class DelveSiteDenizenRenderable(PyswornRenderable):
    def __init__(self, denizen: DelveSiteDenizen):
        self.denizen = denizen

    def _render(self):
        min_ = getattr(self.denizen.roll, "min", "")
        max_ = getattr(self.denizen.roll, "max", "")
        roll = f"{min_}-{max_}"
        frequency = self.denizen.frequency.name.replace("_", " ")
        npc = name_or_id(self.denizen.npc)
        name = self.denizen.name if self.denizen.name else ""

        return f"{roll:^8} |  {frequency} | {npc} |{name}\n"

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        # roll, frequency, npc, name = self._render()
        yield Markdown(self._render())


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
        roll, text = self._render()
        yield f"{roll:^8}{text}"

    def _render(self):
        min_ = getattr(self.feature.roll, "min", "")
        max_ = getattr(self.feature.roll, "max", "")
        return (
            f"{min_}-{max_}",
            f"{self.feature.text}",
        )


class DelveSiteDomainOrThemeRenderable(PyswornRenderable):
    # def __init__(self, theme: DelveSiteTheme | DelveSiteDomain):
    #     self.domain_or_theme = theme
    #     if isinstance(theme, DelveSiteTheme):

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.domain_or_theme.id)
        yield Markdown(getattr(self.domain_or_theme, "summary", ""))
        yield Markdown(getattr(self.domain_or_theme, "description", ""))

        yield ""
        yield Markdown("**FEATURES**")
        for feature in self.domain_or_theme.features:
            yield DelveSiteFeatureRenderable(feature)

        yield ""
        yield Markdown("**DANGERS**")
        for danger in self.domain_or_theme.dangers:
            yield DelveSiteFeatureRenderable(danger)


class DelveSiteThemeRenderable(DelveSiteDomainOrThemeRenderable):
    BORDER_TITLE = "Theme"

    def __init__(self, domain: DelveSiteTheme):
        self.domain_or_theme = domain


class DelveSiteDomainRenderable(DelveSiteDomainOrThemeRenderable):
    BORDER_TITLE = "Domain"

    def __init__(self, theme: DelveSiteDomain):
        self.domain_or_theme = theme


class MoveOutcomeRenderable(PyswornRenderable):
    def __init__(
        self,
        outcome: MoveOutcome,
    ):
        self.outcome = outcome

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.outcome.id)
        yield Markdown(self.outcome.text)


class MoveRenderable(PyswornRenderable):
    def __init__(
        self,
        move: MoveActionRoll
        | MoveNoRoll
        | MoveProgressRoll
        | MoveSpecialTrack
        | EmbeddedMove,
        *,
        outcome: str | None = None,
        **kwargs,
    ):
        self.move = move
        # self.outcome = outcome

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.move.id)
        if isinstance(self.move, MoveProgressRoll) or isinstance(
            self.move, MoveSpecialTrack
        ):
            yield "[b i]Progress Move[/]\n"

        yield from _render_text_with_embeds(self.move.text, self.move.id)

        # if self.outcome:
        # yield Markdown(getattr(self.move.outcomes, self.outcome).text)
        # yield


class MoveCategoryRenderable(CollectionRenderable, PyswornRenderable):
    BORDER_TITLE = "Moves"

    def __init__(self, collection: MoveCategory):
        self.collection = collection


# for Starforged
NPC_CHALLENGE_RANK_STARFORGED = {
    ChallengeRank.int_1: "⬢⬡⬡⬡⬡",
    ChallengeRank.int_2: "⬢⬢⬡⬡⬡",
    ChallengeRank.int_3: "⬢⬢⬢⬡⬡",
    ChallengeRank.int_4: "⬢⬢⬢⬢⬡",
    ChallengeRank.int_5: "⬢⬢⬢⬢⬢",
}
# Classic
NPC_CHALLENGE_RANK = {
    ChallengeRank.int_1: "Troublesome (3 progress per harm; inflicts 1 harm)",
    ChallengeRank.int_2: "Dangerous (2 progress per harm; inflicts 2 harm)",
    ChallengeRank.int_3: "Formidable (1 progress per harm; inflicts 3 harm)",
    ChallengeRank.int_4: "Extreme (2 ticks per harm; inflicts 4 harm)",
    ChallengeRank.int_5: "Epic (1 tick per harm; inflicts 5 harm)",
}


class NpcVariantRenderable(PyswornRenderable):
    def __init__(self, npc: NpcVariant):
        self.npc = npc

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.npc.id)
        # yield f"{self.npc.nature}"

        if "starforged" in self.npc.id:
            yield NPC_CHALLENGE_RANK_STARFORGED[self.npc.rank]
        else:
            yield (Rule(style="white"))
            yield Markdown(f"**Rank:** {NPC_CHALLENGE_RANK[self.npc.rank]}\n\n")
        for feature in ("features", "drives", "tactics"):
            if attrs := getattr(self.npc, feature, None) is None:
                continue
            yield (Rule(style="dim white"))
            yield Markdown(f"**{feature.title()}:**")
            yield Markdown(
                "".join(f"- {item}\n" for item in getattr(self.npc, feature))
            )
        yield (Rule(style="white"))

        if summary := self.npc.summary:
            yield Markdown(f"**{summary}**")

        if description := getattr(self.npc, "description"):
            yield Markdown(description)

        if quest_starter := getattr(self.npc, "quest_starter", None):
            yield Markdown(f"> *Quest Starter: {quest_starter}*")

        if your_truth := getattr(self.npc, "your_truth", None):
            yield Panel(Markdown(f"\n\n**YOUR TRUTH**\n\n**{your_truth}**\n"))


class NpcRenderable(PyswornRenderable):
    def __init__(self, npc: Npc):
        self.npc = npc

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield NpcVariantRenderable(self.npc)
        for variant in self.npc.variants.values():
            yield Panel(NpcVariantRenderable(variant))


class NpcCollectionRenderable(CollectionRenderable, PyswornRenderable):
    def __init__(self, collection: NpcCollection):
        self.collection = collection


class OracleTablesCollectionRenderable(PyswornRenderable):
    BORDER_TITLE = "Oracles"

    def __init__(
        self,
        collection: OracleTablesCollection,
        *,
        roll: str | None = None,
    ):
        self.collection = collection
        self.roll = roll

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.collection.id)
        if summary := self.collection.summary:
            yield Markdown(summary)

        if contents := getattr(self.collection, "contents", None):
            yield ""
            yield "[cyan]" + ", ".join(contents) + "[/]"

        if collections := getattr(self.collection, "collections", None):
            yield ""
            yield "[cyan]" + ", ".join(collections) + "[/]"


class OracleTableSharedRenderable(PyswornRenderable):
    BORDER_TITLE = "Oracles"

    def __init__(
        self,
        collection: OracleTableSharedText
        | OracleTableSharedText2
        | OracleTableSharedRolls,
    ):
        self.shared = collection

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.shared.id)
        if summary := self.shared.summary:
            yield Markdown(summary)

        yield Columns(
            [
                OracleRollableRenderable(oracle)
                for oracle in self.shared.contents.values()
            ]
        )


class OracleRollableRenderable(PyswornRenderable):
    BORDER_TITLE = "Oracle"

    def __init__(
        self,
        table: OracleRollable
        | OracleTableText
        | OracleTableText2
        | OracleTableText3
        | OracleColumnText
        | OracleColumnText2
        | OracleColumnText3
        | EmbeddedOracleRollable
        | EmbeddedOracleColumnText
        | EmbeddedOracleTableText,
        *,
        roll: str | None = None,
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
        if type(self.table).__name__.startswith("Embedded"):
            yield breadcrumbs(self.table._id)

        if summary := getattr(self.table, "summary", None):
            yield Markdown(summary)

        rows = [row._render()[1:] for row in self.rows]
        row_tables = []
        row_styles = ["on black", "on gray11"]

        if "adventures" in self.table.id:
            col_width1 = None
        else:
            col_width1 = max(len(row[1]) for row in rows)

        for row, style in zip(rows, cycle(row_styles)):
            t = Table.grid(padding=(0, 1), pad_edge=False)
            t.add_column(width=8)
            t.add_column(width=col_width1)
            t.add_row(*row, style=style)
            row_tables.append(t)

        yield breadcrumbs(self.table.id)
        yield Columns(
            row_tables,
            # [str(row) for row in self.rows],
            expand=True,
            # equal=True,
            column_first=True,
        )


class OracleRollableRowRenderable(PyswornRenderable):
    def __init__(self, row: OracleRollableRow | OracleRollableRowText):
        self.row = row

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Text.from_markup(str(self))

    def _render(self):
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
        text2 = getattr(self.row, "text2", None)
        text3 = getattr(self.row, "text3", None)

        text = re.sub(r"\[(.+?)\]\(.+?\)", (r"\1").upper(), text)

        num = self.row.id.split(".")[-1]

        if "adventures" in self.row.id:
            if text3:
                return (
                    f"[i dim dark_red]{num:<3}[/]",
                    f"{rtxt:^8}",
                    Markdown(f"**{text}** {text2}\\\n{text3}"),
                )

            if text2:
                return (
                    f"[i dim dark_red]{num:<3}[/]",
                    f"{rtxt:^8}",
                    Markdown(f"**{text}**\\\n{text2}"),
                )
        else:
            if text3:
                return (
                    f"[i dim dark_red]{num:<3}[/]",
                    f"{rtxt:^8}",
                    text,
                    text2,
                    text3,
                )

            if text2:
                return (
                    f"[i dim dark_red]{num:<3}[/]",
                    f"{rtxt:^8}",
                    text,
                    text2,
                )

        return (
            f"[i dim dark_red]{num:<3}[/]",
            f"{rtxt:^8}",
            f"{text}",
        )

    def __str__(self):
        return " ".join(self._render()[1:])


class RarityRenderable(PyswornRenderable):
    def __init__(self, rarity: Rarity):
        self.rarity = rarity

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.rarity.id)
        asset_type = self.rarity.asset.split("/")[1]
        yield Markdown(
            f"{asset_type.upper()}: {name_or_id(self.rarity.asset).upper()} **{self.rarity.xp_cost} XP**\n"
        )
        yield ""
        if description := getattr(self.rarity, "description"):
            yield Markdown(description)


class TruthOptionRenderable(PyswornRenderable):
    def __init__(self, truth: TruthOption):
        self.truth = truth

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        roll = self.truth.roll
        summary = getattr(self.truth, "summary", "")

        table = Table.grid()
        table.add_column(width=8, justify="center")
        table.add_column()

        table.add_row(f"[b]{roll.min}-{roll.max}[/]", Markdown(f"**{summary}**"))
        table.add_row("", "")

        if description := getattr(self.truth, "description", None):
            for d in _render_text_with_embeds(description, self.truth.id):
                table.add_row("", d)

        # oracles = []
        # for oracle in self.truth.oracles.values():
        #     oracles.append(OracleRollableRenderable(oracle))

        table.add_row(
            "", Markdown(f"\n> *Quest Starter: {self.truth.quest_starter}*\n\n")
        )

        yield table


class TruthRenderable(PyswornRenderable):
    def __init__(self, truth: Truth):
        self.truth = truth

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield breadcrumbs(self.truth.id)

        if summary := getattr(self.truth, "summary", None):
            yield Markdown(summary)
            yield Rule()

        for option in self.truth.options:
            yield TruthOptionRenderable(option)
            yield Rule(style="dim white")

        if your_character := getattr(self.truth, "your_character", None):
            yield Markdown(f"♟ {your_character}")

        yield Markdown(f"⚑ {' '.join(faction.text for faction in self.truth.factions)}")


class RulesRenderable(PyswornRenderable):
    def __init__(self, rules: Rules):
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
