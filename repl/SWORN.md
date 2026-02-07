# Sworn Language Reference

## Types

oracle_collection
oracle_rollable
oracle_rollable.row

move_category
move
move.condition      face danger: strong hit
move.outcome
move.oracle_rollable
move.oracle_rollable.row

asset_collection
asset
asset.ability
asset.ability.move
asset.ability.move.condition
asset.ability.move.outcome
asset.ability.oracle_rollable
asset.ability.oracle_rollable.row
atlas_collection
atlas_entry
npc_collection
npc
truth
truth.option
rarity
delve_site
delve_site.denizen
delve_site_theme
delve_site_theme.feature
delve_site_theme.danger
delve_site_domain
delve_site_domain.feature
delve_site_domain.danger
npc.variant
truth.option.oracle_rollable
truth.option.oracle_rollable.row

## Tokens

- keywords
  - pragmas [ ] move to configuration
    - play [rulesetN] ... [ruleset1] # which rulesets to load
    - seed [int] # initialize random number generator
    - match [fuzzy|exact] # how to match rules
  - rules
    - action_roll
    - progress_roll
  - macros
    boost
- reference ids
  - --> built from included rulesets
- variables
  - "\[a-z]\[A-Z][0-9]"
- constants
  - string ["..."]
  - markdown ["""..."""]
