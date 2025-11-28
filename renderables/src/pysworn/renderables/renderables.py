import re

from pysworn.datasworn import breadcrumbs, index
from rich.columns import Columns
from rich.console import Group, RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty
from rich.rule import Rule
from rich.text import Text


class RuleSetRenderable:
    def __init__(self, ruleset):
        self.ruleset = ruleset

    def __rich__(self):
        msg = f"# {self.ruleset.title.value}\n\n"
        msg += f"{self.ruleset.url.value}\n\n"
        msg += f"Licensed for our use under {self.ruleset.license.value}\n\n"
        msg += "Authors: "
        for author in self.ruleset.authors:
            msg += f"{author.name.value} "
            # {author.email.value} {author.url.value}\n"
        return Markdown(msg)


class CollectionRenderable:
    def __init__(self, collection):
        self.collection = collection

    def __rich__(self):
        msg = f"## {self.collection.name.value}\n\n"
        if self.collection.summary:
            msg += f"{self.collection.summary.value}\n\n"
        if self.collection.description:
            msg += f"{self.collection.description.value}\n\n"

        msg += (
            "Oracles: "
            + ", ".join(
                [
                    f"[{v.name.value}]({v.id.value})"
                    for v in self.collection.contents.values()
                ]
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


class AtlasEntryRenderable:
    def __init__(self, atlas_entry):
        self.atlas_entry = atlas_entry

    def __rich__(self):
        msg = f"## {self.atlas_entry.name.value}\n\n"
        msg += f"{self.atlas_entry.summary.value}\n\n"
        msg += f"{self.atlas_entry.description.value}\n\n"
        return Markdown(msg)


class AssetAbilityRenderable:
    def __init__(self, ability):
        self.ability = ability

    def __rich__(self):
        msg = "⬤ " if self.ability.enabled else "◯ "
        msg += f"{self.ability.text.value}\n\n"
        moves = []
        # for move in self.ability.moves:
        #     moves.append(MoveRenderable(move))
        return Group(Markdown(msg), *moves)


class AssetRenderable:
    def __init__(self, asset):
        self.asset = asset

    def __rich__(self):
        msg = f"{self.asset.category.value.upper()} \n{self.asset.name.value.upper()}\n"
        abilities = []
        for ability in self.asset.abilities:
            abilities.append(AssetAbilityRenderable(ability))
        return Group(Text(msg), *abilities)


class DelveSiteRenderable:
    def __init__(self, delve_site):
        self.delve_site = delve_site

    def __rich__(self):
        msg = f"{self.delve_site.category.value.upper()} \n{self.delve_site.name.value.upper()}\n"
        theme = index[self.delve_site.theme.value].name.value
        domain = index[self.delve_site.domain.value].name.value
        region = index[self.delve_site.region.value].name.value
        msg += f"{theme} {domain} in the {region}. "
        msg += f"Rank: {self.delve_site.rank.value}\n\n"
        # denizens = ["| Roll | Frequency | NPC | Name |\n| --- | --- | --- | --- |\n"]
        denizens = "Denizens\n\nRoll | Frequency | NPC | Name\n---|---|---|---\n"
        for denizen in self.delve_site.denizens:
            denizens += str(DelveSiteDenizenRenderable(denizen))
        return Group(Markdown(msg), Rule(style="dim white"), Markdown(denizens))


class DelveSiteDenizenRenderable:
    def __init__(self, denizen):
        self.denizen = denizen

    def __str__(self):
        roll = f"{self.denizen.roll.min}-{self.denizen.roll.max} "
        msg = f"{roll:^7} "
        msg += f"| {self.denizen.frequency.value} "
        if self.denizen.npc:
            npc = index[self.denizen.npc.value].name.value
            msg += f"| {npc} "
        if self.denizen.name:
            msg += f"| {self.denizen.name.value} "

        return msg + "\n"

    def __rich__(self):
        return Markdown(str(self))


class DelveSiteThemeRenderable:
    def __init__(self, theme):
        self.theme = theme

    def __rich__(self):
        msg = f"{self.theme.category.value.upper()} \n{self.theme.name.value.upper()}\n"
        dangers: list[RenderableType] = [Markdown("## Dangers\n\n")]
        for danger in self.theme.dangers:
            dangers.append(DelveSiteFeatureRenderable(danger))
        features: list[RenderableType] = [Markdown("## Features\n\n")]
        for feature in self.theme.features:
            features.append(DelveSiteFeatureRenderable(feature))
        return Group(Markdown(msg), *dangers, *features)  # Markdown(msg)


class DelveSiteDomainRenderable:
    def __init__(self, domain):
        self.domain = domain

    def __rich__(self):
        msg = (
            f"{self.domain.category.value.upper()} \n{self.domain.name.value.upper()}\n"
        )
        dangers: list[RenderableType] = [Markdown("## Dangers\n\n")]
        for danger in self.domain.dangers:
            dangers.append(DelveSiteFeatureRenderable(danger))
        features: list[RenderableType] = [Markdown("## Features\n\n")]
        for feature in self.domain.features:
            features.append(DelveSiteFeatureRenderable(feature))
        return Group(Markdown(msg), *dangers, *features)


class DelveSiteFeatureRenderable:
    def __init__(self, feature):
        self.feature = feature

    def __rich__(self):
        msg = f"{self.feature.roll.min}-{self.feature.roll.max}: {self.feature.text.value} "
        return Markdown(msg)
        # return Pretty(self.feature)


class MoveRenderable:
    def __init__(self, move):
        self.move = move

    def __rich__(self):
        msg = (
            # f"{self.move.category.value.upper()}\n"
            f"{self.move.name.value.upper()}\n\n{self.move.text.value}"
        )
        return Markdown(msg)


class NpcRenderable:
    def __init__(self, npc):
        self.npc = npc

    def __rich__(self):
        msg = " > ".join(breadcrumbs(self.npc.id.value))
        variants = [NpcVariantRenderable(self.npc)]
        for variant in self.npc.variants.values():
            variants.append(NpcVariantRenderable(variant))
        return Group(Markdown(msg), *variants)


class NpcVariantRenderable:
    def __init__(self, npc):
        self.npc = npc

    def __rich__(self):
        msg = (
            f"## {self.npc.name.value}\n\n"
            f"{self.npc.nature.value.value} Rank {self.npc.rank.value}\n\n"
        )
        for attr in ("drives", "features", "tactics"):
            if hasattr(self.npc, attr) and getattr(self.npc, attr):
                msg += f"### {attr.title()}\n\n"
                for item in getattr(self.npc, attr):
                    msg += f"- {item.value}\n"

        if self.npc.summary:
            msg += f"{self.npc.summary.value}\n\n"
        msg += f"{self.npc.description.value}\n\n"
        if hasattr(self.npc, "quest_starter") and self.npc.quest_starter:
            msg += f"> *{self.npc.quest_starter.value}*\n\n"

        return Markdown(msg)
        # return Pretty(self.npc)


class NpcCollectionRenderable:
    def __init__(self, npc_collection):
        self.npc_collection = npc_collection

    def __rich__(self):
        return Pretty(self.npc_collection)


class OracleRollableRenderable:
    def __init__(self, table):
        self.table = table

    def __rich__(self):
        msg = " > ".join(breadcrumbs(self.table.id.value))
        rows = []
        for row in self.table.rows:
            # rows.append(Align(OracleRollableRowRenderable(row), width=54))
            rows.append(OracleRollableRowRenderable(row))
        return Group(
            Markdown(msg),
            Rule(style="dim white"),
            Columns(
                rows,
                expand=True,
                equal=True,
                column_first=True,
            ),
        )


class OracleRollableRowRenderable:
    def __init__(self, row):
        self.row = row

    def __rich__(self):
        return Text.from_markup(str(self))
        # return Markdown(str(self))

    def __str__(self):
        roll = self.row.roll
        if roll:
            roll_min = self.row.roll.min if self.row.roll.min else ""
            roll_max = self.row.roll.max if self.row.roll.max else ""
            roll = f"{roll_min}-{roll_max}"
        else:
            roll = ""

        text = self.row.text.value
        text = re.sub(r"\[(.+?)\]\(.+?\)", (r"\1").upper(), text)

        msg = f"{roll:^7} {text}"
        # if self.row.text2:
        #     msg += f"{self.row.text2.value} "
        # if self.row.text3:
        #     msg += f"{self.row.text3.value}"
        return msg


class RarityRenderable:
    def __init__(self, rarity):
        self.rarity = rarity

    def __rich__(self):
        asset = index[self.rarity.asset.value]
        msg = (
            f"**{self.rarity.name.value}** "
            # f"[{asset.name.value}]({self.rarity.asset.value})"
            f"for {asset.name.value.upper()} "
            f"(XP cost: {self.rarity.xp_cost})\n\n"
            f"---\n\n"
            f"{self.rarity.description.value}\n\n"
        )
        return Markdown(msg)


class TruthOptionRenderable:
    def __init__(self, truth):
        self.truth = truth

    def __rich__(self):
        msg = ""
        roll = self.truth.roll
        msg += f"**{roll.min}-{roll.max}** "
        if self.truth.summary:
            msg += f"**{self.truth.summary.value}**\n\n"
        msg += f"{self.truth.description.value}\n\n"
        oracles = []
        for oracle in self.truth.oracles.values():
            oracles.append(OracleRollableRenderable(oracle))
        msg2 = f"\n> *{self.truth.quest_starter.value}*\n\n"
        return Group(Markdown(msg), *oracles, Markdown(msg2))


class TruthRenderable:
    def __init__(self, truth):
        self.truth = truth

    def __rich__(self):
        name = f"# {self.truth.name.value}"
        your_character = ""
        if hasattr(self.truth, "your_character") and self.truth.your_character:
            your_character = f"> *{self.truth.your_character.value}*\n\n"
        options = []
        for option in self.truth.options:
            options.append(TruthOptionRenderable(option))
            options.append(Rule(style="dim white"))
        return Group(Markdown(name), *options, Markdown(your_character))


class RulesRenderable:
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
                        rules.append(Markdown(f"### {v.label.value}"))
                    rules.append(Markdown(v.description.value))
                    # rules.append(Pretty(v))
        return Group(*rules)
