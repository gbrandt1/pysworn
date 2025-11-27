from pysworn.renderables.renderables import (
    AssetAbilityRenderable,
    AssetRenderable,
    AtlasEntryRenderable,
    CollectionRenderable,
    DelveSiteDenizenRenderable,
    DelveSiteDomainRenderable,
    DelveSiteFeatureRenderable,
    DelveSiteRenderable,
    DelveSiteThemeRenderable,
    MoveRenderable,
    # NpcCollectionRenderable,
    NpcRenderable,
    NpcVariantRenderable,
    OracleRollableRenderable,
    OracleRollableRowRenderable,
    RarityRenderable,
    RuleSetRenderable,
    RulesRenderable,
    TruthOptionRenderable,
    TruthRenderable,
)


def get_renderable(id_: str):
    from pysworn.datasworn import index
    from rich.pretty import Pretty

    obj = index[id_]
    rule_type = id_.split(":")[0]
    renderable = RENDERABLES.get(rule_type)
    if not renderable:
        return Pretty(obj, max_depth=2, expand_all=True)
    return renderable(obj)


RENDERABLES = {
    "asset": AssetRenderable,
    "asset.ability": AssetAbilityRenderable,
    "asset.ability.move": MoveRenderable,
    "asset.ability.oracle_rollable": OracleRollableRenderable,
    "asset.ability.oracle_rollable.row": OracleRollableRowRenderable,
    "asset_collection": CollectionRenderable,
    "atlas_collection": CollectionRenderable,
    "atlas_entry": AtlasEntryRenderable,
    "classic": RuleSetRenderable,
    "delve": RuleSetRenderable,
    "delve_site": DelveSiteRenderable,
    "delve_site.denizen": DelveSiteDenizenRenderable,
    "delve_site_domain": DelveSiteDomainRenderable,
    "delve_site_domain.danger": DelveSiteFeatureRenderable,
    "delve_site_domain.feature": DelveSiteFeatureRenderable,
    "delve_site_theme": DelveSiteThemeRenderable,
    "delve_site_theme.danger": DelveSiteFeatureRenderable,
    "delve_site_theme.feature": DelveSiteFeatureRenderable,
    "move": MoveRenderable,
    "move.oracle_rollable": OracleRollableRenderable,
    "move.oracle_rollable.row": OracleRollableRowRenderable,
    "move_category": CollectionRenderable,
    "npc": NpcRenderable,
    "npc.variant": NpcVariantRenderable,
    "npc_collection": CollectionRenderable,
    "oracle_collection": CollectionRenderable,
    "oracle_rollable": OracleRollableRenderable,
    "oracle_rollable.row": OracleRollableRowRenderable,
    "rarity": RarityRenderable,
    "starforged": RuleSetRenderable,
    "starsmith": RuleSetRenderable,
    "sundered_isles": RuleSetRenderable,
    "truth": TruthRenderable,
    "truth.option": TruthOptionRenderable,
    "truth.option.oracle_rollable": OracleRollableRenderable,
    "truth.option.oracle_rollable.row": OracleRollableRowRenderable,
    "rules": RulesRenderable,
}

__all__ = [
    "get_renderable",
    "RENDERABLES",
]
