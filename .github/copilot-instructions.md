# PySworn Codebase Instructions for AI Agents

## Project Overview

PySworn is a terminal UI application for navigating Ironsworn: Starforged TTRPG content. It uses a **monorepo workspace structure** with four interdependent packages:

- **`datasworn/`**: Loads and indexes Datasworn JSON rulesets (classic, delve, starforged, starsmith, sundered_isles)
- **`reference/`**: Textual TUI for browsing rules, oracles, assets, moves, NPCs
- **`renderables/`**: Rich-library rendering classes for different rule types
- **`journal/`**: (Stub) Future journaling functionality

## Architecture Patterns

### 1. Content Distribution via Datasworn Index

All rule content flows through a centralized `index` dictionary keyed by IDs like `"oracle_rollable:starforged/oracles/region"`. The `RulesServer` class (`datasworn/main.py`) loads all JSON files in parallel threads on startup:

- Thread-safe loading via `ThreadPoolExecutor`
- Global `rules` dict maps ruleset IDs to `RulesPackage` objects
- `add_to_index()` recursively indexes all nested dataclass objects

**Key implication**: ID lookups are critical - validate IDs exist in `index` before accessing. Use `get_parent_id(id_)` to traverse hierarchies.

### 2. Viewer Architecture Pattern

Content rendering uses a **registry-based visitor pattern**:

- `VIEWER_TYPES` dict in `reference/__init__.py` maps rule ID prefixes to `(category, ViewerClass)` tuples
- Each viewer type (e.g., `OracleViewer`, `AssetViewer`) renders content for a specific rule category
- `RENDERABLES` dict in `renderables/__init__.py` maps prefixes to `*Renderable` classes for Rich rendering

**When adding new rule types**: Register in both `VIEWER_TYPES` and `RENDERABLES` registries.

### 3. Dataclass-First Design

Ironsworn content is defined as frozen dataclasses (from `datasworn._datasworn` stubs). Key patterns:

- Most objects have `name: TextType`, `id: IDType`, `summary/description: TextType` attributes
- Rich text is wrapped in `.value` properties (e.g., `oracle.name.value`)
- Relationships use ID references; resolve via `index[id_string]` lookup
- Many fields are optional; check `hasattr()` before accessing

## Development Workflow

### Build & Run

```bash
# Install dependencies (uv workspace management)
uv sync

# Run dev mode (hot-reload for Textual)
uv run --active textual run --dev -c pysworn

# Run datasworn CLI inspector
uv run datasworn

# Interactive console for debugging
uv run --active textual console
```

### Testing

```bash
# Run tests (async enabled)
uv run pytest

# With coverage
uv run pytest --cov=pysworn
```

### Code Quality

```bash
# Format & lint fixes
uv run --active ruff check --fix
```

**Note**: `--active` flag runs within the workspace environment context.

## Project Conventions

- **Package organization**: Each workspace member is a distinct package (`pysworn-datasworn`, `pysworn-reference`, etc.)
- **ID semantics**: Format is `type:ruleset/category/subcategory` (e.g., `"oracle_rollable:starforged/oracles/region"`)
- **Licensing**: Content under CC-BY-NC-SA-4.0; code under MIT. License info embedded in JSON via `source` property.
- **Async patterns**: Tests use pytest-asyncio with auto mode; TUI operations are inherently async (Textual framework)
- **Rich rendering**: All terminal output uses `rich` library; renderables inherit from Rich's rendering protocol

## Key Files & Patterns

| Purpose             | File                                                                                      |
| ------------------- | ----------------------------------------------------------------------------------------- |
| Core indexing logic | `datasworn/src/pysworn/datasworn/main.py` (RulesServer, add_to_index, get_parent_id)      |
| TUI entry point     | `reference/src/pysworn/reference/app.py` (PyswornApp, theme setup)                        |
| Viewer registry     | `reference/src/pysworn/reference/__init__.py` (VIEWER_TYPES mapping)                      |
| Rich renderers      | `renderables/src/pysworn/renderables/renderables.py` (all \*Renderable classes)           |
| Content navigation  | `reference/src/pysworn/reference/screen.py` (ReferenceScreen, tabs for rule categories)   |
| Styling             | `reference/src/pysworn/reference/*.tcss` (Textual CSS; markdown.tcss for markdown panels) |

## Common Tasks

**Adding a new rule viewer**: Create `NewRuleViewer` in `reference/viewer.py`, add to `VIEWER_TYPES`, create `NewRenderable` in `renderables/renderables.py`, add to `RENDERABLES`.

**Debugging rule lookup failures**: Check ID format in `VIEWER_TYPES`; ensure indexed content exists via `python -c "from pysworn.datasworn import index; print(index.get('rule_id'))"`.

**Textual debugging**: Use `textual console` REPL to inspect widgets live or add `log.debug()` statements (logged via `TextualHandler`).

**Styling updates**: Edit `.tcss` files; hot-reloads in dev mode. Reference classes via CSS class names assigned in `compose()` methods.

## External Dependencies

- **Textual**: TUI framework (widgets, async rendering, CSS styling)
- **Rich**: Terminal rendering (colors, markdown, tables, panels)
- **Typer**: CLI framework for datasworn CLI tool
- **orjson**: Fast JSON loading for ruleset files
- **dataclasses**: Frozen dataclass stubs for Ironsworn rules (generated from Datasworn JSON schema)
