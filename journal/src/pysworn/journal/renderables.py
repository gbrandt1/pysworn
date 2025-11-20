from re import A, M

from pysworn.datasworn import index
from rich.console import Group
from rich.markdown import Markdown


class RuleSetRenderable:
    def __init__(self, ruleset):
        self.ruleset = ruleset

    def __rich__(self):
        msg = f"# {self.ruleset.title.value}\n\n"
        msg += f"{self.ruleset.url.value}\n\n"
        msg += f"{self.ruleset.license.value}\n\n"
        msg += "Authors: "
        for author in self.ruleset.authors:
            msg += f"{author.name.value} "
            # {author.email.value} {author.url.value}\n"
        return Markdown(msg)


class AssetAbilityRenderable:
    def __init__(self, ability):
        self.ability = ability

    def __rich__(self):
        msg = "* " if self.ability.enabled else "o "
        msg += f"{self.ability.text.value}\n\n"
        moves = []
        # for move in self.ability.moves:
        #     moves.append(MoveRenderable(move))
        return Group(Markdown(msg), *moves)


class AssetRenderable:
    def __init__(self, asset):
        self.asset = asset

    def __rich__(self):
        msg = f"{self.asset.category.value} {self.asset.name.value}\n\n"
        abilities = []
        for ability in self.asset.abilities:
            abilities.append(AssetAbilityRenderable(ability))
        return Group(Markdown(msg), *abilities)


class MoveRenderable:
    def __init__(self, move):
        self.move = move

    def __rich__(self):
        msg = f"# {self.move.name.value}\n\n{self.move.text.value}\n\n"
        return Markdown(msg)


class OracleRollableRenderable:
    def __init__(self, table):
        self.table = table

    def __rich__(self):
        msg = f"## {self.table.name.value}\n\n"
        # msg += f"{self.table.roll} {self.table.text.value}"
        rows = []
        for row in self.table.rows:
            rows.append(OracleRollableRowRenderable(row))
        return Group(Markdown(msg), *rows)


class OracleRollableRowRenderable:
    def __init__(self, row):
        self.row = row

    def __rich__(self):
        msg = f"{self.row.roll.min}-{self.row.roll.max}: {self.row.text.value} "
        # if self.row.text2:
        #     msg += f"{self.row.text2.value} "
        # if self.row.text3:
        #     msg += f"{self.row.text3.value}"
        return Markdown(msg)


class RarityRenderable:
    def __init__(self, rarity):
        self.rarity = rarity

    def __rich__(self):
        asset = index[self.rarity.asset.value]
        msg = (
            f"**{self.rarity.name.value}** "
            f"XP cost: {self.rarity.xp_cost} "
            f"[{asset.name.value}]({self.rarity.asset.value})"
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
        your_character = f"> *{self.truth.your_character.value}*\n\n"
        options = []
        for option in self.truth.options:
            options.append(TruthOptionRenderable(option))
        return Group(Markdown(name), *options, Markdown(your_character))


RENDERABLES = {
    "asset": AssetRenderable,
    "asset.ability": AssetAbilityRenderable,
    "asset.ability.move": MoveRenderable,
    "asset.ability.oracle_rollable": OracleRollableRenderable,
    "asset.ability.oracle_rollable.row": OracleRollableRowRenderable,
    "asset_collection": None,
    "atlas_collection": None,
    "atlas_entry": None,
    "classic": RuleSetRenderable,
    "delve": RuleSetRenderable,
    "delve_site": None,
    "delve_site.denizen": None,
    "delve_site_domain": None,
    "delve_site_domain.danger": None,
    "delve_site_domain.feature": None,
    "delve_site_theme": None,
    "delve_site_theme.danger": None,
    "delve_site_theme.feature": None,
    "move": MoveRenderable,
    "move.oracle_rollable": OracleRollableRenderable,
    "move.oracle_rollable.row": OracleRollableRowRenderable,
    "move_category": None,
    "npc": None,
    "npc.variant": None,
    "npc_collection": None,
    "oracle_collection": None,
    "oracle_rollable": OracleRollableRenderable,
    "oracle_rollable.row": OracleRollableRowRenderable,
    "rarity": RarityRenderable,
    "starforged": RuleSetRenderable,
    "starsmith": RuleSetRenderable,
    "sundered_isles": RuleSetRenderable,
    "truth": TruthRenderable,
    "truth.option": TruthOptionRenderable,
    "truth.option.oracle_rollable": None,
    "truth.option.oracle_rollable.row": OracleRollableRowRenderable,
    "rules": None,
}
