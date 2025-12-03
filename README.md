# PySworn

## Description

PySworn is a set of terminal applications written in Python based on [datasworn](https://github.com/rsek/datasworn) and  [Textual](https://textual.textualize.io/) to play [Ironsworn: Starforged](https://tomkinpress.com/pages/ironsworn-starforged) the tabletop roleplaying game by Shawn Tomkin.
For full attribution see the bottom of this README.

## Installation

### Local Installation

`uv` is recommended for toolchain management.

For installation, clone the repository and execute `uv sync` in the root directory (which depends on the individual packages).

You can then activate the virtual environment or use `uv run` to start the applications.

## Usage

The following executables are provided:

| Name | Description
| --- | ---
| `pysworn` | Reference Browser.
| `pysworn-v2` | Reference Browser (new version under development).
| `datasworn` | Inspect the [datasworn](https://github.com/rsek/datasworn) JSON files used by PySworn.
| `renderables` | PySworn Ironsworn:Starforged Rich Renderables dumping tool.

### Direct Installation

Alternatively you can run directly from this repository

```uvx --from git+https://github.com/gbrandt1/pysworn.git#subdirectory=reference pysworn```

```uvx --from git+https://github.com/gbrandt1/pysworn.git#subdirectory=reference pysworn-v2 -i```

```uvx --from git+https://github.com/gbrandt1/pysworn.git#subdirectory=datasworn datasworn```

```uvx --no-cache --from git+https://github.com/gbrandt1/pysworn.git#subdirectory=renderables renderables```

### PySworn Ironsworn:Starforged Reference Application

`uv run pysworn`

This tool opens a [Textual](https://textual.textualize.io/) application to quickly navigate oracles and other content for Ironsworn: Starforged.

### Datasworn Tool

`uv run datasworn`

This tool can be used to inspect the [datasworn](https://github.com/rsek/datasworn) JSON files used by PySworn.

## Attribution

This work is based on "Ironsworn: Starforged", created by Shawn Tomkin, and licensed for our use under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International license (<https://creativecommons.org/licenses/by-nc-sa/4.0/).​>

Datasworn JSON packaging by rsek and Textual by Will McGugan et al. are based on a MIT License.

The package itself is licensed under the MIT License.
