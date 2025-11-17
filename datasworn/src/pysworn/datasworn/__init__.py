from ._datasworn import *  # noqa

from .main import RULESETS, get_parent_id, get_rule_types, index, rules
from ._rich import RichPrintOracleRollableRowText

RICH_PRINTERS = {
    "asset": None,
    "asset.ability": None,
    "asset.ability.move": None,
    "asset.ability.oracle_rollable": None,
    "asset.ability.oracle_rollable.row": RichPrintOracleRollableRowText,
    "asset_collection": None,
    "atlas_collection": None,
    "atlas_entry": None,
    "classic": None,
    "delve": None,
    "delve_site": None,
    "delve_site.denizen": None,
    "delve_site_domain": None,
    "delve_site_domain.danger": None,
    "delve_site_domain.feature": None,
    "delve_site_theme": None,
    "delve_site_theme.danger": None,
    "delve_site_theme.feature": None,
    "move": None,
    "move.oracle_rollable": None,
    "move.oracle_rollable.row": RichPrintOracleRollableRowText,
    "move_category": None,
    "npc": None,
    "npc.variant": None,
    "npc_collection": None,
    "oracle_collection": None,
    "oracle_rollable": None,
    "oracle_rollable.row": RichPrintOracleRollableRowText,
    "rarity": None,
    "starforged": None,
    "starsmith": None,
    "sundered_isles": None,
    "truth": None,
    "truth.option": None,
    "truth.option.oracle_rollable": None,
    "truth.option.oracle_rollable.row": RichPrintOracleRollableRowText,
    "rules": None,
}


__all__ = [
    "index",
    "get_parent_id",
    "rules",
    "get_rule_types",
    "RULESETS",
]
