from re import M

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
        msg += f"Authors: "
        for author in self.ruleset.authors:
            msg += f"{author.name.value} "
            # {author.email.value} {author.url.value}\n"
        return Markdown(msg)


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
        msg = f"# {self.table.name.value}\n\n"
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
        if self.row.text2:
            msg += f"{self.row.text2.value} "
        if self.row.text3:
            msg += f"{self.row.text3.value}"
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


RENDERABLES = {
    "asset": None,
    "asset.ability": None,
    "asset.ability.move": None,
    "asset.ability.oracle_rollable": None,
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
    "truth": None,
    "truth.option": None,
    "truth.option.oracle_rollable": None,
    "truth.option.oracle_rollable.row": OracleRollableRowRenderable,
    "rules": None,
}
