# Pysworn ToDo

ClassVars:

- [x] Moves: Embedded oracles not yet deserialized
  - [ ] conditions fully deserialized?
- [ ] Moves: Show embedded moves?
- [ ] resolve links in table rows
- [x] extra column for roll (?)
- [ ] move row rendering to renderables

- [x] Rich theme
  - [x] markdown tables border color
- [ ] sync Rich theme and Textual theme

- [x] render tables with sync. zebra along row --> copy of Rich Columns

- [ ] define access to embedded objects (with '.' in type)

## REPL

- [ ] load/save history
- [ ] tab completion
- [ ] prompt toolkit? [ ] Textual input
- [ ] syntax highlighting
- [ ] support '.' to suppress output

## Matcher

- [ ] right-aligned table
- [ ] call from resolver
- [ ] fat-finger correction?

## Commands

- [ ] support args/kwargs in commands

### tree

- [ ] tree by path

### $

- [ ] color ids
- [ ] syntax highlight

## Renderables

- [ ] add tests
- [ ] widths --> move to CSS (in Textual), args in Rich
- [ ] panels --> move to CSS (in Textual)
- [ ] correct rendering of column-wise Shared tables
  - [x] allow options (args, kwargs)
    - [x] control panel
    - [ ] verbosity options
- [ ] RulesetRenderable
  - [ ] panel [ ] info in two-columns layout

## Mechanics

- [ ] integrate rules (add ids?)
- [ ] meters
- [ ] progress tracks
- [ ] special tracks
- [ ] tags --> [ ] contexts

### roll + Rollables

- [ ] add tests
- [ ] add missing rollables
- [ ] move row rendering to renderables
- [ ] enable free rolling with dice code
- [ ] oracles
  - [ ] render as single table
  - [ ] resolve rerolls or defers ("roll twice", "action + theme" etc.)

### Inventory

- [ ] support random inventory

## Rulesets

### Classic

### Delve

- [x] Delve Site Themes & Domains
- [x] p 94 "Site Starters" table missing
- [x] p 200 3 Rarities missing

### Starforged

- [ ] Truths: Embedded oracles not yet deserialized
- [ ] p 100 (resolve links)  
- [ ] NPC Variant render order, summary ?

tables

- [ ] sector name page --> 302
- [ ] show num rolls

- [ ] collections
  - [ ] planets on one page?
  - [ ] derelict areas on one page?
  - [ ] location themes on one page?
  - [ ] shared tables
    - [ ] correctly render columns OracleTableSharedText, OracleTableSharedRolls
- [ ] use cursed tag
- [ ] p 320 planetside peril?
- [ ] sources / page numbers in tables within collections
- [ ] separate columns correctly

### Sundered Isles

- [ ] p 14 Asset Guide missing
- [ ] Truths missing summary attribute
- [ ] Oracles missing summary attribute
- [ ] truths as table?

- [x] p 150 Highlands table entries above 50 missing
- [ ] Faction templates missing
- [ ] Character Role on one page

### FE Runners

- [ ] stray '}}' in Find an Opportunity, Reveal a Danger

### Ancient Wonders

- [ ] finalize reordering
