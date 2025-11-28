import random

from pysworn.datasworn import index, rules
from pysworn.datasworn._datasworn import (
    Asset,
    AtlasCollection,
    AtlasEntry,
    DelveSiteDomain,
    DelveSiteTheme,
    Rarity,
    Ruleset,
    SpecialTrackType,
)
from pysworn.datasworn.main import get_parent_id
from pysworn.reference.oracle import get_max_row_widths
from rich.rule import Rule
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ItemGrid, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import DataTable, Label, Markdown, Static, Switch

from ._rich import markdown, markup
from .oracle_table import OracleTable

RANKS = {
    1: "Troublesome (3 progress per harm; inflicts 1 harm)",
    2: "Dangerous (2 progress per harm; inflicts 2 harm)",
    3: "Formidable (1 progress per harm; inflicts 3 harm)",
    4: "Extreme (2 ticks per harm; inflicts 4 harm)",
    5: "Epic (1 tick per harm; inflicts 5 harm)",
}


def render_tags(rule_id) -> ComposeResult:
    obj = index[rule_id]
    if hasattr(obj, "tags") and obj.tags:
        for ruleset, value in obj.tags.value.items():
            if ruleset not in rules:
                ruleset = "sundered_isles"
                continue
            tag_rules = rules[ruleset].rules.tags
            msg = ""
            for tag, targets in value.items():
                if tag not in tag_rules:
                    msg += f"**{tag} not found** {targets}\n"
                    continue

                msg += f"*{markdown(tag_rules[tag].description)}* "
                # msg += f"{targets.value}"

                if isinstance(targets.value, list):
                    for target in targets.value:
                        try:
                            t = index[target]
                            msg += f"*[{t.name.value}]({target})* "
                        except KeyError:
                            msg += f"*{target}*"
                else:
                    try:
                        target = index[targets.value]
                        msg += f"*[{markdown(target.name)}]({targets.value})*\n"
                    except KeyError:
                        msg += f"*{targets.value}*"
                # yield Pretty(value)
            yield RuleMarkdown(msg)


def render_suggestions(rule_id) -> ComposeResult:
    obj = index[rule_id]
    if hasattr(obj, "suggestions") and obj.suggestions:
        msg = []
        for s in obj.suggestions.value:
            if s.value in index:
                sobj = index[s.value]
                msg.append(f"[{sobj.name.value}]({s.value})")
            else:
                msg.append(f"{s.value}")
    yield RuleMarkdown(", ".join(msg))


class RuleMarkdown(Markdown):
    """
    taken from:
    https://github.com/Textualize/textual/discussions/4227
    """

    can_focus = False
    can_focus_children = False

    BINDINGS = [
        Binding("enter", "enable_focus_children"),
        Binding("escape", "disable_focus_children"),
        Binding("m", "focus_next", priority=True),
        Binding("n", "focus_previous", priority=True),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.open_links = False

    # def on_ready(self) -> None:
    def action_enable_focus_children(self) -> None:
        self.can_focus_children = True
        for child in self.children:
            child.can_focus = True
        self.children[0].focus()

    def action_disable_focus_children(self) -> None:
        self.can_focus_children = False
        for child in self.children:
            child.can_focus = False
        self.focus()

    def action_focus_next(self) -> None:
        self.screen.focus_next("RuleMarkdown *")

    def action_focus_previous(self) -> None:
        self.screen.focus_previous("RuleMarkdown *")


class RuleViewer(VerticalScroll):
    can_focus_children = True
    BINDINGS = [
        Binding("r", "roll", "Roll", show=True),
    ]

    id_map: dict[str, str] = {}
    """Map of widget IDs to rule IDs."""

    class Highlighted(Message):
        def __init__(self, link: str):
            self.link = link
            super().__init__()

    class Selected(Message):
        def __init__(self, link: str):
            self.link = link
            super().__init__()

    def __init__(self, rule_id: str, **kwargs):
        super().__init__(**kwargs)
        self.rule_id = rule_id

    def compose(self) -> ComposeResult:
        self.id_map["rule-header"] = self.rule_id
        obj = index[self.rule_id]
        if hasattr(obj, "color") and obj.color:
            self.styles.border_title_color = obj.color.value
            self.styles.border = ("solid", obj.color.value)

        if hasattr(obj, "canonical_name") and obj.canonical_name:
            yield RuleMarkdown(f"**{obj.canonical_name.value.upper()}**\n\n")
        elif hasattr(obj, "name") and obj.name:
            yield RuleMarkdown(f"**{obj.name.value.upper()}**\n\n")

        if hasattr(obj, "type") and isinstance(obj.type, str):
            self.border_title = obj.type.upper()
        if hasattr(obj, "summary") and obj.summary:
            yield RuleMarkdown(f"**{markdown(obj.summary)}**")
        if hasattr(obj, "description") and obj.description:
            yield RuleMarkdown(f"{markdown(obj.description)}")
        if hasattr(obj, "suggestions") and obj.suggestions:
            yield from render_suggestions(self.rule_id)
        if hasattr(obj, "comment") and obj.comment:
            yield RuleMarkdown(f"*{obj.comment}*")
        # if hasattr(obj, "tags") and obj.tags:
        #     yield from render_tags(self.rule_id)
        # if hasattr(obj, "oracle") and obj.oracle:
        #     yield OracleTable(obj)
        if hasattr(obj, "source") and obj.source:
            source = f"[i]{obj.source.title.value}"
            # source = f"[i][{obj.source.title.value}]({obj.source.url.value})"
            if obj.source.page:
                source += f" page {obj.source.page.value}"

            self.border_subtitle = source

    async def action_debug(self):
        self.debug = not self.debug
        self.log(f"Debug Mode {'enabled' if self.debug else 'disabled'}")

    async def action_roll(self):
        """
        Placeholder for roll action.
        This should be implemented in subclasses where needed.
        """
        self.log("Roll action triggered, but not implemented.")

    def on_focus(self, event):
        event.stop()
        self.post_message(self.Selected(self.rule_id))

    def on_key(self, event):
        if event.key == "enter":
            event.stop()
            self.post_message(self.Selected(self.rule_id))

    def on_oracle_table_selected(self, event):
        self.post_message(self.Selected(f"{event.row_id}"))

    def on_oracle_table_Highlighted(self, event):
        self.post_message(self.Highlighted(f"{event.row_id}"))


class RulesetViewer(RuleViewer):
    ruleset: Ruleset

    def compose(self):
        yield from super().compose()
        self.ruleset = index[self.rule_id]
        r = self.ruleset
        msg = f"This work is based on **{markdown(r.title)}**, "
        for author in r.authors:
            msg += f"created by {author.name.value} {author.email or ''} {author.url or ''} {r.date.strftime('%Y')}, "
        msg += (
            f"and licensed for our use under "
            f"[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International license]({r.license.value}).\n\n"
        )

        msg += f"For the original game visit {markdown(r.url)}.\n\n"
        msg += (
            f"This work uses the official JSON Files from "
            f"[Datasworn Version {r.datasworn_version.value}](https://github.com/rsek/datasworn/tree/v0.1.0)."
        )
        yield RuleMarkdown(msg)

    def on_markdown_link_clicked(self, event):
        event.stop()


class OracleCollectionViewer(RuleViewer):
    can_focus = False

    def compose(self):
        yield from super().compose()

        collection = index[self.rule_id]
        self.wmax = 0
        with ItemGrid(min_column_width=30):
            for oracle in collection.contents.values():
                oracle = index[oracle.id.value]
                max1, max2, max3 = get_max_row_widths(oracle)
                self.wmax = max(max1, max2, max3)
                yield EmbeddedOracleViewer(oracle.id.value, classes="embedded-oracle")

        if hasattr(collection, "collections"):
            for collection in collection.collections.values():
                yield RuleMarkdown(
                    f"- [{markdown(collection.name)}]({collection.id.value}) "
                    f"{markdown(collection.summary)}\n"
                )

    def on_mount(self):
        # self.log(f"OracleCollectionViewer {self.rule_id} wmax {self.wmax}")
        try:
            grid = self.query_one(ItemGrid)
            grid.min_column_width = min(self.wmax + 8, 50)
        except Exception:
            pass


class OracleViewer(RuleViewer):
    can_focus = False

    def compose(self):
        # oracle = index[self.rule_id]
        yield from super().compose()
        yield OracleTable(self.rule_id, id="oracle-table1")

        yield from render_tags(self.rule_id)


class EmbeddedOracleViewer(OracleViewer):
    can_focus = False
    can_focus_children = True

    # def on_mount(self):
    # table = self.query_one(OracleTable)
    # table.show_header = False


def compose_condition(condition) -> str:
    text = ""
    if not (hasattr(condition, "roll_options") and condition.roll_options):
        return text
    for roll_option in condition.roll_options:
        text += " or " if text else ""

        if roll_option.using == "stat":
            stat = markdown(roll_option.stat.value)
            text += f"Roll +[{stat}]({stat})."

        elif roll_option.using == "condition_meter":
            meter = roll_option.condition_meter.value.value

            text += f"Roll +[{meter}]({meter})."

        elif isinstance(roll_option.using, SpecialTrackType):
            track = roll_option.using.value.value

            text += f"Roll against [{track.replace('_', ' ')}]({track})"

        elif roll_option.using == "attached_asset_control":
            text += f"Roll against attached asset {roll_option.control.value}"

        elif roll_option.using == "asset_control":
            text += "Roll against "
            if roll_option.assets:
                text += " or ".join(asset.value for asset in roll_option.assets)
            else:
                text += "asset"
            text += f" {roll_option.control.value}"

        elif roll_option.using == "asset_option":
            text += "Roll against "
            if roll_option.assets:
                text += " or ".join(asset.value for asset in roll_option.assets)
            else:
                text += "asset"
            text += f" {roll_option.option.value}"

        elif roll_option.using == "custom":
            text += f"Roll {roll_option.value} {roll_option.label.value}"

        elif roll_option.using.value == "progress_track":
            text += f"Roll against {roll_option.using.value}"
        else:
            msg = roll_option.using
            raise NotImplementedError(msg)
    return text


def compose_trigger(trigger) -> str:
    text = ""
    if hasattr(trigger, "text") and trigger.text:
        text = markdown(trigger.text)
    for condition in trigger.conditions:
        text += "\n- "
        method = ""
        if hasattr(condition, "method") and condition.method:
            method = condition.method.value
        if condition.text:
            text += markdown(condition.text)
        text += f" {compose_condition(condition)}"
        if method and method != "player_choice":
            text += f" ({method.replace('_', ' ')})"
    return f"{text}."


class MoveOutcome(Markdown, can_focus=True):
    outcome: str

    def __init__(self, *args, outcome: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcome = outcome

    def on_key(self, event):
        if event.key == "enter":
            self.post_message(RuleViewer.Selected(self.outcome))


class MoveViewer(RuleViewer):
    def compose(self) -> ComposeResult:
        yield from super().compose()
        self.move = index[self.rule_id]
        move = self.move
        self.border_title = move.name.value.upper()
        self.border_subtitle = f"{move.roll_type.title().replace('_', ' ')}"

        if hasattr(move, "replaces") and move.replaces:
            with Vertical(classes="move-replaces"):
                for replace in move.replaces:
                    target = index[replace.value]
                    yield RuleMarkdown(
                        f"*Replaces [{target.name.value}]({replace.value})*",
                        classes="move-replace",
                    )

        if move.roll_type == "no_roll":
            yield RuleMarkdown(
                markdown(move.text),
                classes="move-name",
            )
        else:
            # Triggers
            if hasattr(move, "trigger") and move.trigger:
                yield RuleMarkdown(compose_trigger(move.trigger))

            # Momentum Burn
            if hasattr(move, "allow_momentum_burn") and move.allow_momentum_burn:
                with Horizontal(classes="move-burn-momentum-container"):
                    yield Switch(
                        id="burn-momentum", value=False, classes="burn-momentum-switch"
                    )
                    yield Label(" Burn Momentum", classes="burn-momentum-label")

            # Outcomes
            if hasattr(move, "outcomes") and move.outcomes:
                with Vertical(classes="move-outcomes"):
                    yield MoveOutcome(
                        markdown(move.outcomes.strong_hit.text),
                        outcome=f"{self.rule_id};strong_hit",
                        id="outcome-strong-hit",
                        classes="move-outcome",
                    )
                    yield MoveOutcome(
                        markdown(move.outcomes.weak_hit.text),
                        outcome=f"{self.rule_id};weak_hit",
                        id="outcome-weak-hit",
                        classes="move-outcome",
                    )
                    yield MoveOutcome(
                        markdown(move.outcomes.miss.text),
                        outcome=f"{self.rule_id};miss",
                        id="outcome-miss",
                        classes="move-outcome",
                    )

        # Embedded Oracles
        if hasattr(move, "oracles"):
            for oracle in move.oracles.values():
                self.log(f"Embedded oracle: {oracle.id.value}")
                yield EmbeddedOracleViewer(oracle.id.value, classes="move-oracle")

    def on_markdown_link_clicked(self, event):
        event.stop()
        if ":" in event.href:
            # Link to another rule
            self.post_message(RuleViewer.Selected(event.href))
        else:
            link = f"{self.move.id.value};{event.href}"
            self.post_message(RuleViewer.Selected(link))


class MoveCategoryViewer(RuleViewer):
    def compose(self) -> ComposeResult:
        yield from super().compose()
        categories = index[self.rule_id]

        for move in categories.contents.values():
            m = index[move.id.value]

            msg = f"## [{markdown(m.name)}]({m.id.value})\n"
            msg += f"{markdown(m.text)}"
            yield RuleMarkdown(msg, classes="move-text")

            yield Static(Rule(characters="━", style="black"))


class AssetAbilityViewer(RuleViewer):
    def compose(self) -> ComposeResult:
        ability = index[self.rule_id]
        yield from super().compose()

        txt = "⬡ "
        if ability.name:
            txt = f"{txt} **{markdown(ability.name)}:**"
        yield RuleMarkdown(
            f"{txt} {markdown(ability.text)}",
        )

        if ability.moves:
            for move in ability.moves.values():
                yield MoveViewer(move.id.value, classes="embedded-move")

        if ability.oracles:
            for oracle in ability.oracles.values():
                yield OracleViewer(oracle.id.value, classes="embedded-oracle")

    # if ability.enhance_moves:
    #     for enhance_move in ability.enhance_moves:
    #         text = "Enhances "
    #         if enhance_move.enhances:
    #             for e in enhance_move.enhances:
    #                 if e.value in index:
    #                     em = index[e.value]
    #                     text += f"[{em.name.value}]({e.value}) "
    #                 else:
    #                     text += f"{e.value} "
    #         if hasattr(enhance_move, "trigger") and enhance_move.trigger:
    #             text += compose_trigger(enhance_move.trigger)
    #         yield RuleMarkdown(
    #             f"{text}",
    #             classes="asset-ability",
    #         )


class AssetViewer(RuleViewer):
    asset: Asset

    def compose(self) -> ComposeResult:
        yield from super().compose()

        if self.rule_id.split(":")[0] == "asset.ability":
            asset_id = get_parent_id(self.rule_id)
            if not asset_id:
                msg = f"AssetViewer: asset.ability {self.rule_id} requires a parent asset id"
                raise ValueError(msg)
            asset = index[asset_id]
        else:
            asset = index[self.rule_id]

        if hasattr(asset, "requirement") and asset.requirement:
            yield RuleMarkdown(f"{markdown(asset.requirement)}")

        # Abilities
        if hasattr(asset, "abilities") and asset.abilities:
            with Vertical(classes="asset-abilities"):
                for ability in asset.abilities:
                    yield AssetAbilityViewer(ability.id.value)

        # Controls
        if hasattr(asset, "controls") and asset.controls:
            for control in asset.controls.values():
                text = f"{control.label.value.title()}: "
                if control.field_type == "condition_meter":
                    if hasattr(control, "max") and control.max:
                        text += " " + "⬡" * (control.max + 1)  # ⬢
                if control.field_type == "checkbox":
                    text += "[] {control.label.value}"
                # if hasattr(control, "field_type") and control.field_type:
                #     text += f"{control.field_type}"
                if hasattr(control, "controls") and control.controls:
                    for k, v in control.controls.items():
                        if k == "out_of_action":
                            text += f"{markdown(v.value)} []"
                        else:
                            text += f"- {k} {v}"
                if hasattr(control, "moves") and control.moves:
                    if control.moves.recover:
                        text += f" [Recover]({control.moves.recover[0].value})"
                    if control.moves.suffer:
                        text += f" [Suffer]({control.moves.suffer[0].value})"
                yield RuleMarkdown(
                    text,
                    classes="asset-control",
                )
        # Tags
        yield from render_tags(self.rule_id)


class AssetCollectionViewer(RuleViewer):
    def compose(self) -> ComposeResult:
        yield from super().compose()
        collection = index[self.rule_id]
        with ItemGrid(min_column_width=54):
            for asset in collection.contents.values():
                yield AssetViewer(asset.id.value)


def render_variant(self, v) -> ComposeResult:
    msg = ""

    msg += f"---\n**Rank:** {RANKS[v.rank.value]} {markdown(v.nature.value)}\n\n"

    if hasattr(v, "features") and v.features:
        msg += "**Features:**\n"
        for f in v.features:
            msg += f"- {markdown(f)}\n"

    if hasattr(v, "drives") and v.drives:
        msg += "\n**Drives:**\n"
        for d in v.drives:
            msg += f"- {markdown(d)}\n"

    if hasattr(v, "tactics") and v.tactics:
        msg += "\n**Tactics:**\n"
        for t in v.tactics:
            msg += f"- {markdown(t)}\n"

    msg += "---\n"
    yield RuleMarkdown(msg)


class NpcVariantViewer(RuleViewer):
    def compose(self):
        v = index[self.rule_id]
        yield from super().compose()
        yield from render_variant(self, v)


class NpcViewer(RuleViewer):
    def compose(self):
        # yield from super().compose()
        npc = index[self.rule_id]

        msg = f"# {npc.name.value.upper()}\n\n"
        yield RuleMarkdown(msg, classes="npc-name")

        yield from render_variant(self, npc)

        if hasattr(npc, "description") and npc.description:
            yield RuleMarkdown(f"{markdown(npc.description)}\n")

        if hasattr(npc, "variants") and npc.variants:
            for variant in npc.variants.values():
                yield NpcVariantViewer(variant.id.value)

        if hasattr(npc, "quest_starter") and npc.quest_starter:
            yield RuleMarkdown(f"> *Quest Starter: {markdown(npc.quest_starter)}*\n")

        if hasattr(npc, "your_truth") and npc.your_truth:
            yield RuleMarkdown(f"**YOUR TRUTH**\n\n**{markdown(npc.your_truth)}**\n")


class NpcCollectionViewer(RuleViewer):
    def compose(self):
        collection = index[self.rule_id]
        yield from super().compose()
        for npc in collection.contents.values():
            n = index[npc.id.value]

            msg = f"- [{markdown(n.name)}]({n.id.value})\n"
            # if hasattr(n, "description"):
            #     msg += f"{markdown(n.description)}"
            yield RuleMarkdown(msg, classes="npc-text")


class TruthOptionViewer(RuleViewer):
    def compose(self):
        self.option = index[self.rule_id]
        option = self.option
        roll = option.roll
        self.border_title = f"◯ {roll.min}-{roll.max}"

        # with Horizontal(classes="truth-option"):
        # with Vertical():
        yield from super().compose()
        if hasattr(option, "quest_starter") and option.quest_starter:
            yield RuleMarkdown(f"> *{markup(option.quest_starter)}*")

        if option.oracles:
            for oracle in option.oracles.values():
                yield EmbeddedOracleViewer(oracle.id.value, classes="embedded-oracle")

    async def action_roll(self):
        await self.parent.action_roll()


class TruthViewer(RuleViewer):
    BINDINGS = [Binding("r", "roll", "Roll", show=True)]

    def compose(self):
        self.truth = index[self.rule_id]
        yield from super().compose()
        truth = self.truth

        if hasattr(self.truth, "options") and self.truth.options:
            for option in truth.options:
                yield TruthOptionViewer(option.id.value)

        if hasattr(truth, "your_character") and truth.your_character:
            yield RuleMarkdown(
                f"> *{markdown(truth.your_character)}*",
            )

        if hasattr(truth, "factions") and truth.factions:
            factions = []
            for faction in truth.factions:
                factions.append(markdown(faction.text))
            yield RuleMarkdown(
                f"> *{'⚑ ' + ' '.join(factions)}*",
            )

    def on_mount(self):
        self.log(self.tree)

    async def action_roll(self):
        options = self.query_children(TruthOptionViewer)
        n = random.randint(0, len(options) - 1)
        selected: TruthOptionViewer | None = None
        for option in options:
            if int(option.rule_id[-1]) == n:
                selected = option
                break
        if selected:
            self.log(f"Rolled for truth {n} --> {selected.rule_id}")
            self.post_message(self.Selected(selected.rule_id))
            selected.focus()

    def on_click(self, event):
        # self.log(event.widget.ancestors)
        # self.log(self.options)
        for ancestor in event.widget.ancestors:
            if ancestor.id and ancestor.id.startswith("truth-option-"):
                option_id = self.options[int(ancestor.id[-1])]
                self.log(f"Option selected {option_id}")
                self.post_message(self.Selected(option_id))
                break

        event.stop()

    def on_markdown_table_of_contents_updated(self, event):
        event.stop()


class AtlasEntryViewer(RuleViewer):
    atlas_entry: AtlasEntry

    def compose(self):
        yield from super().compose()
        self.atlas_entry = index[self.rule_id]
        ae = self.atlas_entry
        msg = f"{markdown(ae.description)}\n"
        for feature in ae.features:
            msg += f"- {markdown(feature)}\n"
        if ae.quest_starter:
            msg += f"\n> *{markdown(ae.quest_starter)}*"

        yield RuleMarkdown(msg)


class AtlasViewer(RuleViewer):
    collection: AtlasCollection

    def compose(self) -> ComposeResult:
        yield from super().compose()
        self.collection = index[self.rule_id]
        collection = self.collection

        for n, atlas_entry in enumerate(collection.contents.values(), start=1):
            ae = index[atlas_entry.id.value]

            msg = (
                f"**{n} [{markdown(ae.name)}]({ae.id.value}):** {markdown(ae.summary)}"
            )
            yield RuleMarkdown(msg, classes="atlas-entry-summary")


class DelveSiteViewer(RuleViewer):
    RANK = {
        1: "",
        2: "Dangerous",
        3: "Formidable",
        4: "Extreme",
        5: "Epic",
    }

    def render_link(self, name: str, link: str) -> str:
        if link in index:
            target = index[link]
            return f"{name} [{markdown(target.name)}]({link})\n\n"
        else:
            return f"{name}({link})\n\n"

    def compose(self):
        delve_site = index[self.rule_id]

        text = f"**Rank:** {self.RANK[delve_site.rank.value]}\n\n"
        text += self.render_link("**Theme:**", delve_site.theme.value)
        text += self.render_link("**Domain:**", delve_site.domain.value)
        text += self.render_link("**Region:**", delve_site.region.value)
        yield RuleMarkdown(text)
        yield from super().compose()

        # text = f"# {markup(delve_site.name)}"

        text = "## Denizens\n"
        text += "Roll |  Name | NPC\n"
        text += " ---|---|--- \n"
        for denizen in delve_site.denizens:
            name = denizen.name.value if denizen.name else ""
            npc = ""
            if denizen.npc:
                if denizen.npc.value not in index:
                    npc = f"({denizen.npc.value})"
                else:
                    target = index[denizen.npc.value]
                    npc = f"[{markdown(target.name)}]({denizen.npc.value})"
            text += (
                f" {markup(denizen.frequency)} "
                f"{denizen.roll.min:3}-{denizen.roll.max:3} "
                f" | {name}| {npc}\n"
            )

        yield RuleMarkdown(text)


def render_table(title: str, items) -> ComposeResult:
    table: DataTable = DataTable(classes="site-table")
    # table.border_title = title
    table.add_column("Roll")
    table.add_column(title)
    table.add_column("Suggestions")
    for feature in items:
        suggestions = []
        if feature.suggestions:
            for suggestion in feature.suggestions.value:
                if suggestion.value not in index:
                    suggestions += f"{suggestion.value} "
                else:
                    target = index[suggestion.value]
                    m0 = target.name.value
                    m1 = suggestion.value
                    suggestions.append(
                        f"[u][@click=screen.open_link('{m1}')]{m0}[/][/u]"
                    )
        table.add_row(
            f"{feature.roll.min:3}-{feature.roll.max:3}",
            markdown(feature.text),
            ", ".join(suggestions),
        )
    yield table


class SiteDomainViewer(RuleViewer):
    site_domain: DelveSiteDomain

    def compose(self) -> ComposeResult:
        yield from super().compose()
        site_domain = index[self.rule_id]
        yield from render_table("Feature", site_domain.features)
        yield from render_table("Danger", site_domain.dangers)
        if site_domain.name_oracle:
            yield RuleMarkdown("[Name Oracle](site_domain.name_oracle.value)\n")
            # yield EmbeddedOracleViewer(
            #     site_domain.name_oracle.value, classes="embedded-oracle"
            # )
        # if site_domain.theme_oracle:
        #     yield EmbeddedOracleViewer(
        #         site_domain.theme_oracle.value, classes="embedded-oracle"
        #     )


class SiteThemeViewer(RuleViewer):
    sitetheme: DelveSiteTheme

    def compose(self) -> ComposeResult:
        yield from super().compose()
        self.site_theme = index[self.rule_id]
        yield RuleMarkdown("**FEATURES**\n")
        yield from render_table("Feature", self.site_theme.features)
        yield RuleMarkdown("**DANGERS**\n")
        yield from render_table("Danger", self.site_theme.dangers)


class RarityViewer(RuleViewer):
    rarity: Rarity

    def compose(self) -> ComposeResult:
        rarity = index[self.rule_id]
        asset = index[rarity.asset.value]
        yield RuleMarkdown(
            f"[{asset.category.value.upper()}: {asset.name.value.upper()}]({rarity.asset.value}) "
        )
        yield RuleMarkdown(f"{rarity.xp_cost} XP")
        yield from super().compose()
