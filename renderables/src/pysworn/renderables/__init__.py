import enum

from .renderables import (
    RENDERABLE_TYPES,
    AssetAbilityRenderable,
    AssetCollectionRenderable,
    AssetRenderable,
    AtlasCollectionRenderable,
    AtlasEntryRenderable,
    CategoryRenderable,
    CollectionRenderable,
    DelveSiteDenizenRenderable,
    DelveSiteDomainRenderable,
    DelveSiteFeatureRenderable,
    DelveSiteRenderable,
    DelveSiteThemeRenderable,
    MoveRenderable,
    NpcCollectionRenderable,
    NpcRenderable,
    NpcVariantRenderable,
    OracleRollableRenderable,
    OracleRollableRowRenderable,
    RarityRenderable,
    RuleSetRenderable,
    RulesRenderable,
    TruthOptionRenderable,
    TruthRenderable,
    get_renderable,
)

# RENDERABLE_KEYS: dict[str, type] = {
#     "asset": AssetRenderable,
#     "asset.ability": AssetAbilityRenderable,
#     "asset.ability.move": MoveRenderable,
#     "asset.ability.oracle_rollable": OracleRollableRenderable,
#     "asset.ability.oracle_rollable.row": OracleRollableRowRenderable,
#     "asset_collection": AssetCollectionRenderable,
#     "atlas_collection": AtlasCollectionRenderable,
#     "atlas_entry": AtlasEntryRenderable,
#     "category": CategoryRenderable,
#     "classic": RuleSetRenderable,
#     "delve": RuleSetRenderable,
#     "delve_site": DelveSiteRenderable,
#     "delve_site.denizen": DelveSiteDenizenRenderable,
#     "delve_site_domain": DelveSiteDomainRenderable,
#     "delve_site_domain.danger": DelveSiteFeatureRenderable,
#     "delve_site_domain.feature": DelveSiteFeatureRenderable,
#     "delve_site_theme": DelveSiteThemeRenderable,
#     "delve_site_theme.danger": DelveSiteFeatureRenderable,
#     "delve_site_theme.feature": DelveSiteFeatureRenderable,
#     "move": MoveRenderable,
#     "move.oracle_rollable": OracleRollableRenderable,
#     "move.oracle_rollable.row": OracleRollableRowRenderable,
#     "move_category": CollectionRenderable,
#     "npc": NpcRenderable,
#     "npc.variant": NpcVariantRenderable,
#     "npc_collection": NpcCollectionRenderable,
#     "oracle_collection": CollectionRenderable,
#     "oracle_rollable": OracleRollableRenderable,
#     "oracle_rollable.row": OracleRollableRowRenderable,
#     "rarity": RarityRenderable,
#     "rules": RulesRenderable,
#     "starforged": RuleSetRenderable,
#     "starsmith": RuleSetRenderable,
#     "sundered_isles": RuleSetRenderable,
#     "truth": TruthRenderable,
#     "truth.option": TruthOptionRenderable,
#     "truth.option.oracle_rollable": OracleRollableRenderable,
#     "truth.option.oracle_rollable.row": OracleRollableRowRenderable,
#     # special keys
# }


class RenderableKeyEnum(enum.Enum):
    ASSET = "asset"
    ASSET_ABILITY = "asset.ability"
    ASSET_ABILITY_MOVE = "asset.ability.move"
    ASSET_ABILITY_ORACLE_ROLLABLE = "asset.ability.oracle_rollable"
    ASSET_ABILITY_ORACLE_ROLLABLE_ROW = "asset.ability.oracle_rollable.row"
    ASSET_COLLECTION = "asset_collection"
    ATLAS_COLLECTION = "atlas_collection"
    ATLAS_ENTRY = "atlas_entry"
    CLASSIC = "classic"
    DELVE = "delve"
    DELVE_SITE = "delve_site"
    DELVE_SITE_DENIZEN = "delve_site.denizen"
    DELVE_SITE_DOMAIN = "delve_site_domain"
    DELVE_SITE_DOMAIN_DANGER = "delve_site_domain.danger"
    DELVE_SITE_DOMAIN_FEATURE = "delve_site_domain.feature"
    DELVE_SITE_THEME = "delve_site_theme"
    DELVE_SITE_THEME_DANGER = "delve_site_theme.danger"
    DELVE_SITE_THEME_FEATURE = "delve_site_theme.feature"
    MOVE = "move"
    MOVE_ORACLE_ROLLABLE = "move.oracle_rollable"
    MOVE_ORACLE_ROLLABLE_ROW = "move.oracle_rollable.row"
    MOVE_CATEGORY = "move_category"
    NPC = "npc"
    NPC_VARIANT = "npc.variant"
    NPC_COLLECTION = "npc_collection"
    ORACLE_COLLECTION = "oracle_collection"
    ORACLE_ROLLABLE = "oracle_rollable"
    ORACLE_ROLLABLE_ROW = "oracle_rollable.row"
    RARITY = "rarity"
    STARFORGED = "starforged"
    STARSMITH = "starsmith"
    SUNDERED_ISLES = "sundered_isles"
    TRUTH = "truth"
    TRUTH_OPTION = "truth.option"
    TRUTH_OPTION_ORACLE_ROLLABLE = "truth.option.oracle_rollable"
    TRUTH_OPTION_ORACLE_ROLLABLE_ROW = "truth.option.oracle_rollable.row"
    RULES = "rules"
    # special keys
    CATEGORY = "category"
    ALL = "all"
    RULESETS = "rulesets"


__all__ = [
    "get_renderable",
    "RENDERABLE_TYPES",
    "AssetAbilityRenderable",
    "AssetCollectionRenderable",
    "AssetRenderable",
    "AtlasCollectionRenderable",
    "AtlasEntryRenderable",
    "CategoryRenderable",
    "CollectionRenderable",
    "DelveSiteDenizenRenderable",
    "DelveSiteDomainRenderable",
    "DelveSiteFeatureRenderable",
    "DelveSiteRenderable",
    "DelveSiteThemeRenderable",
    "MoveRenderable",
    "NpcCollectionRenderable",
    "NpcRenderable",
    "NpcVariantRenderable",
    "OracleRollableRenderable",
    "OracleRollableRowRenderable",
    "RarityRenderable",
    "RuleSetRenderable",
    "RulesRenderable",
    "TruthOptionRenderable",
    "TruthRenderable",
]
