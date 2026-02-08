import logging
import re
from inspect import getfullargspec
from itertools import cycle
from operator import ge
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
from rich.pretty import Pretty
from rich.rule import Rule
from rich.table import Column, Table
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
    last = id_.split("/")[-1].replace(".", " ")
    return f"{last.title().replace('_', ' ')}"


def breadcrumbs(id_: str):
    if ":" not in id_:
        return index[id_].name
    yield Text.from_markup(f"[b]{name_or_id(id_).upper()}[/] ").append(
        id_, style="log.path"
    )
    yield ""


def get_renderable(obj: BaseModel, *args: Any, **kwargs: Any) -> RenderableType | str:
    r_type = type(obj)
    renderable = RENDERABLE_TYPES.get(r_type, None)
    if renderable:
        border_title: str = renderable.BORDER_TITLE.upper()
        if category := getattr(obj, "category", None):
            border_title = f"{category.upper()}"  # {border_title}"
        # border_title = f"{border_title} {name_or_id(obj.id)}"

        subtitle = ""
        if source := getattr(obj, "source", None):
            subtitle = f"[{source.title}, {source.page}]"

        border_style = "scope.border"
        if hasattr(obj, "color") and obj.color:
            border_style = obj.color

        return Panel(
            renderable(obj, *args, **kwargs),
            title=border_title,
            title_align="left",
            subtitle=subtitle or "",
            subtitle_align="right",
            border_style=border_style,
            width=renderable.MAX_WIDTH,
        )

    return f"No renderable found for {type(obj)} ({getattr(obj, 'id', None)})"


def render_text_with_embeds(
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
        # elif id_embed not in index:
        # yield Markdown(f"- **{oracle_id}**", style="red")
        #     yield Markdown(f"- {oracle_id}")
        # elif oracle := index[id_]:
        else:
            if obj := index.get(id_embed, None):
                renderable = RENDERABLE_TYPES.get(type(obj), None)
                if renderable:
                    yield ""
                    yield renderable(obj)
            else:
                yield Markdown(f"- **{oracle_id}**", style="red")
        #     yield Markdown(f"- Oracle {oracle_id} not found")


class PyswornRenderable(ConsoleRenderable):
    BORDER_TITLE: ClassVar[str | None] = None
    MAX_WIDTH: ClassVar[int | None] = None
    """Default max. width to provide line-wrapping similar to books."""

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)

        fullargspec = getfullargspec(cls.__init__)
        for k, v in fullargspec.annotations.items():
            log.debug(f"{k}: {v.__class__} {v}")
            cls._resolve_type(v)

        if not cls.BORDER_TITLE:
            cls.BORDER_TITLE = re.sub(
                r"([a-z\d])([A-Z])", r"\1 \2", cls.__name__.replace("Renderable", "")
            )

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
        yield Markdown(f"# {self.ruleset.title}")
        yield Markdown(f"[{self.ruleset.url}]({self.ruleset.url})")
        msg = "by "
        for author in self.ruleset.authors:
            msg += f"{author.name}"
            if author.email:
                msg += f" ({author.email})"
            if author.url:
                msg += f" {author.url}"
        yield Markdown(msg)
        yield Markdown(f"Licensed for our use under {self.ruleset.license}")
        yield ""

        collections: list[tuple[str, int]] = []
        for k in self.ruleset.model_fields_set:
            d = getattr(self.ruleset, k)
            if isinstance(d, dict) and d:
                collections.append((k, len(d)))

        # ids = [i for i in datasworn_tree.index if self.ruleset.id in i]

        yield Markdown(
            "Contains "
            + ", ".join(f"{n} {k.title()}" for k, n in collections)
            + " collections."
        )


class CategoryRenderable(PyswornRenderable):
    def __init__(self, category: dict[str, Any], *ar, **kwargs):
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
        yield from breadcrumbs(self.collection.id)
        # yield Markdown(f"**{self.collection.name.upper()}**")

        if summary := getattr(self.collection, "summary", None):
            yield Markdown(f"**{summary}**")
            yield ""

        if contents := getattr(self.collection, "contents", None):
            yield ", ".join(c.title().replace("_", " ") for c in contents)

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

    def __init__(self, collection: AtlasCollection, *args, **kwargs):
        self.collection = collection


class AtlasEntryRenderable(PyswornRenderable):
    BORDER_TITLE = "Atlas Entry"

    def __init__(self, atlas_entry: AtlasEntry, *args, **kwargs):
        self.atlas_entry = atlas_entry

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.atlas_entry.id)
        if self.atlas_entry.summary:
            yield Markdown(self.atlas_entry.summary)


class AssetAbilityRenderable(PyswornRenderable):
    def __init__(self, ability: AssetAbility, *args, **kwargs):
        self.ability = ability

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        t = Table.grid(padding=(0, 1), pad_edge=False)
        t.add_row(
            # "⬤" if self.ability.enabled else "◯", Markdown(f"{self.ability.text}")
            "⬢" if self.ability.enabled else "⬡",
            Markdown(f"{self.ability.text}"),
        )
        yield t

        # for move in self.ability.moves.values():
        # yield (MoveRenderable(move))

        for oracle in self.ability.oracles.values():
            yield ""
            yield OracleRollableRenderable(oracle)


class AssetRenderable(PyswornRenderable):
    MAX_WIDTH = 50

    def __init__(self, asset: Asset, *args, **kwargs):
        self.asset = asset

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.asset.id)

        if requirement := getattr(self.asset, "requirement", None):
            yield Markdown(f"**{requirement}**")
            yield ""

        for option in self.asset.options.values():
            l = option.label.title()
            yield f"{l}{'_' * (self.MAX_WIDTH - len(l) - 4)}"
            yield ""
            # match option.field_type.name:
            #     case "role_name":

        for ability in self.asset.abilities:
            yield AssetAbilityRenderable(ability)
            yield ""

        for control in self.asset.controls.values():
            match control.field_type.name:
                case "checkbox":
                    yield f"⬡ {control.label.title()}"
                case "condition_meter":
                    yield f"{'⬡' * (control.max - control.min + 1)} {control.label.title()}"
                case "card_flip":
                    yield f"⬡ {control.label.title()}"
                case "select_enhancement":
                    yield f"{control.label.title()}"
                    for choice in control.choices:
                        yield f"- {choice}"
                case _:
                    yield Pretty(control)

        if replaces := getattr(self.asset, "replaces", None):
            yield Markdown(f"**Replaces: {', '.join(replaces)}*")


class AssetCollectionRenderable(PyswornRenderable):
    BORDER_TITLE = "Asset Type"

    def __init__(self, collection: AssetCollection, *args, **kwargs):
        self.collection = collection

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.collection.id)

        if summary := getattr(self.collection, "summary", None):
            yield Markdown(f"**{summary}**")
            yield ""

        assets = []
        if contents := getattr(self.collection, "contents", None):
            for asset in self.collection.contents.values():
                # assets.append(get_renderable(asset))
                assets.append(asset.name)
            yield Columns(assets)

        # if collections := getattr(self.collection, "collections", None):
        #     for collection in self.collection.collections.values():
        #         collections.append(CollectionRenderable(collection))
        #     yield Group(
        #         Panel(
        #             Group(*collections),
        #             border_style="dim",
        #         ),
        #     )


class DelveSiteRenderable(PyswornRenderable):
    BORDER_TITLE = "Site"
    MAX_WIDTH = 86

    def __init__(self, delve_site: DelveSite, *args, **kwargs):
        self.delve_site = delve_site

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.delve_site.id)
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
    def __init__(self, denizen: DelveSiteDenizen, *args, **kwargs):
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
        *args,
        **kwargs,
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
    MAX_WIDTH = 50

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.domain_or_theme.id)
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

    def __init__(self, domain: DelveSiteTheme, *args, **kwargs):
        self.domain_or_theme = domain


class DelveSiteDomainRenderable(DelveSiteDomainOrThemeRenderable):
    BORDER_TITLE = "Domain"

    def __init__(self, theme: DelveSiteDomain, *args, **kwargs):
        self.domain_or_theme = theme


class MoveConditionRenderable(PyswornRenderable):
    def __init__(
        self,
        condition: TriggerSpecialTrackCondition
        | TriggerProgressRollCondition
        | TriggerActionRollCondition,
        *args,
        breadcrumbs: bool = True,
        **kwargs,
    ):
        self.condition = condition

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.condition.id)

        msg = []
        if text := getattr(self.condition, "text", None):
            msg.append(text)
        # yield Markdown(msg)

        match self.condition:
            case TriggerSpecialTrackCondition():
                for roll_option in self.condition.roll_options:
                    msg.append(roll_option.using)

            case TriggerProgressRollCondition():
                for roll_option in self.condition.roll_options:
                    msg.append(roll_option.using)

            case TriggerActionRollCondition():
                for roll_option in self.condition.roll_options:
                    using = roll_option.using.value
                    # msg.append(using)

                    if not roll_option.__pydantic_extra__:
                        msg.append(Pretty(roll_option))
                        continue
                    if using in (
                        "stat",
                        "condition_meter",
                    ):
                        msg.append(f" +{roll_option.__pydantic_extra__[using]}")
                        continue
                    if using in (
                        "asset_control",
                        # "asset_option",
                        "attached_asset_control",
                        # "attached_asset_option",
                    ):
                        msg.append(f" +{roll_option.__pydantic_extra__['control']}")
                        continue
                    if using == "custom":
                        msg.append(f" +{roll_option.__pydantic_extra__['label']}")
                        continue
                    msg.append(Pretty(roll_option))

                # asset_option = 'asset_option'
                # attached_asset_option = 'attached_asset_option'

            case _:
                yield Pretty(self.condition)
                # raise NotImplementedError

        if method := getattr(self.condition, "method", None):
            msg.append(f"({method.value.replace('_', ' ')})")

        yield Markdown(" ".join(msg))


class MoveOutcomeRenderable(PyswornRenderable):
    def __init__(
        self,
        outcome: MoveOutcome,
        *args,
        breadcrumbs: bool = True,
        **kwargs,
    ):
        self.outcome = outcome

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.outcome.id)
        yield Markdown(self.outcome.text)


class MoveRenderable(PyswornRenderable):
    MAX_WIDTH = 68

    def __init__(
        self,
        move: MoveActionRoll
        | MoveNoRoll
        | MoveProgressRoll
        | MoveSpecialTrack
        | EmbeddedMove
        | EmbeddedActionRollMove
        | EmbeddedSpecialTrackMove,
        *args,
        **kwargs,
    ):
        self.move = move
        # self.outcome = outcome

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.move.id)
        if isinstance(
            self.move, MoveProgressRoll | MoveSpecialTrack | EmbeddedSpecialTrackMove
        ):
            yield "[b i]Progress Move[/]\n"

        yield from render_text_with_embeds(self.move.text, self.move.id)


class MoveCategoryRenderable(CollectionRenderable, PyswornRenderable):
    BORDER_TITLE = "Moves"

    def __init__(self, collection: MoveCategory, *args, **kwargs):
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
    def __init__(self, npc: NpcVariant, *args, **kwargs):
        self.npc = npc

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.npc.id)
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
    MAX_WIDTH = 88

    def __init__(
        self,
        npc: Npc,
        *args,
        variants: bool = True,
        **kwargs,
    ):
        self.npc = npc
        self.variants = variants

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield NpcVariantRenderable(self.npc)
        if not self.variants:
            return
        for variant in self.npc.variants.values():
            yield (Rule(style="dim white"))
            yield get_renderable(variant)


class NpcCollectionRenderable(CollectionRenderable, PyswornRenderable):
    def __init__(self, collection: NpcCollection, *args, **kwargs):
        self.collection = collection


class OracleTablesCollectionRenderable(PyswornRenderable):
    BORDER_TITLE = "Oracles"

    def __init__(
        self,
        collection: OracleTablesCollection,
        *args,
        roll: str | None = None,
        **kwargs,
    ):
        self.collection = collection
        self.roll = roll

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.collection.id)
        if summary := self.collection.summary:
            yield Markdown(summary)

        if contents := getattr(self.collection, "contents", None):
            yield "Oracles: " + ", ".join(c.title() for c in contents)

        if collections := getattr(self.collection, "collections", None):
            yield "Collections: " + ", ".join(c.title() for c in collections)


class OracleTableSharedRenderable(PyswornRenderable):
    BORDER_TITLE = "Oracles"

    def __init__(
        self,
        collection: OracleTableSharedText
        | OracleTableSharedText2
        | OracleTableSharedRolls,
        *args,
        **kwargs,
    ):
        self.shared = collection

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.shared.id)
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
        *args,
        **kwargs,
    ):
        self.oracle = table
        self.rows = [OracleRollableRowRenderable(row) for row in self.oracle.rows]

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        if not type(self.oracle).__name__.startswith("Embedded"):
            yield from breadcrumbs(self.oracle.id)

        if summary := getattr(self.oracle, "summary", None):
            yield Markdown(summary)

        rows = [row._render()[1:] for row in self.rows]
        row_tables = []
        row_styles = ["on black", "on gray11"]

        if "adventures" in self.oracle.id:
            col_width1 = None
        else:
            col_width1 = max(len(row[1]) for row in rows)

        if cl := getattr(self.oracle, "column_labels", None):
            if text2 := getattr(cl, "text2", ""):
                t = Table.grid(
                    Column(width=8, min_width=8),
                    Column(width=col_width1),
                    padding=(0, 1),
                    pad_edge=False,
                )
                t.add_row(
                    cl.roll,
                    cl.text,
                    getattr(cl, "text2", ""),
                    getattr(cl, "text3", ""),
                    style="bold on black",
                )
                row_tables.append(t)
                row_tables.append(Rule(style="white"))

        for row, style in zip(rows, cycle(row_styles)):
            t = Table.grid(
                Column(min_width=8, justify="center"),
                Column(
                    max_width=col_width1,
                    overflow="fold",
                ),
                padding=(0, 1),
                pad_edge=False,
            )
            t.add_row(*row, style=style)
            row_tables.append(t)

        yield Columns(
            row_tables,
            # [str(row) for row in self.rows],
            expand=True,
            # equal=True,
            column_first=True,
        )


class OracleRollableRowRenderable(PyswornRenderable):
    def __init__(
        self,
        row: OracleRollableRowText | OracleRollableRowText2 | OracleRollableRowText3,
        result: int | None = None,
        *args,
        **kwargs,
    ):
        self.row = row
        self.result = result

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Text.from_markup(str(self))

    def _render(self):
        if self.result:
            rtxt = f"[b]{self.result}:[/]"
        else:
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
                    f"[b]{text}[/] {text2}\\\n{text3}",
                )

            if text2:
                return (
                    f"[i dim dark_red]{num:<3}[/]",
                    f"{rtxt:^8}",
                    f"[b]{text}[/]\\\n{text2}",
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
    MAX_WIDTH = 82

    def __init__(self, rarity: Rarity, *args, **kwargs):
        self.rarity = rarity

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.rarity.id)
        asset_type = self.rarity.asset.split("/")[1]
        yield Markdown(
            f"{asset_type.upper()}: {name_or_id(self.rarity.asset).upper()} **{self.rarity.xp_cost} XP**\n"
        )
        yield ""
        if description := getattr(self.rarity, "description"):
            yield Markdown(description)


class TruthOptionRenderable(PyswornRenderable):
    def __init__(
        self,
        truth: TruthOption,
        *args,
        show_quest_starter: bool = False,
        **kwargs,
    ):
        self.truth = truth
        self.show_quest_starter = show_quest_starter

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        roll = self.truth.roll

        table = Table.grid()
        table.add_column(width=8, justify="center")
        table.add_column()

        rcol = []
        if summary := getattr(self.truth, "summary", None):
            rcol.append(Markdown(f"**{summary}**"))
            rcol.append("")

        # table.add_row(f"[b]{roll.min}-{roll.max}[/]", Markdown(f"**{summary}**"))
        # table.add_row("", "")

        if description := getattr(self.truth, "description", None):
            for d in render_text_with_embeds(description, self.truth.id):
                rcol.append(d)

        # oracles = []
        # for oracle in self.truth.oracles.values():
        #     oracles.append(OracleRollableRenderable(oracle))

        if self.show_quest_starter and (
            quest_starter := getattr(self.truth, "quest_starter", None)
        ):
            rcol.append(Markdown(f"> *Quest Starter: {quest_starter}*"))

        table.add_row(f"[b]{roll.min}-{roll.max}[/]", Group(*rcol))
        yield table


class TruthRenderable(PyswornRenderable):
    MAX_WIDTH = 80

    def __init__(self, truth: Truth, *args, **kwargs):
        self.truth = truth

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from breadcrumbs(self.truth.id)

        if summary := getattr(self.truth, "summary", None):
            yield Markdown(summary)
            yield Rule()

        for option in self.truth.options:
            yield TruthOptionRenderable(option)
            yield Rule(style="dim white")

        if your_character := getattr(self.truth, "your_character", None):
            yield Markdown(f"♟ {your_character}")

        if factions := getattr(self.truth, "factions", None):
            yield ""
            yield Markdown(f"⚑ {' '.join(faction.text for faction in factions)}")


class RulesRenderable(PyswornRenderable):
    def __init__(self, rules: Rules, *args, **kwargs):
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
