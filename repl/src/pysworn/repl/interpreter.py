import logging
import re
from functools import singledispatchmethod
from typing import Any

from pysworn.common import datasworn_tree
from pysworn.renderables import get_renderable
from pysworn.repl.grammar import (
    DocString,
    Expr,
    # Pragma,
    ExprStmt,
    KeywordStmt,
    Literal,
)
from pysworn.repl.roller import get_roller
from pysworn.repl.theme import pysworn_theme
from pysworn.repl.utils import (
    depth_first_merge,
    fuzzy_search,
    get_id_tree,
    id_to_tokens,
)

# from rich import print
from rich.console import Console
from rich.pretty import Pretty

log = logging.getLogger(__name__)
console = Console(theme=pysworn_theme)

print = console.print

# global interpreter state
state: dict[str, Any] = {
    "rulesets": set(),  # TODO: needs to be list to keep preference order
    "paths": {},
}


def build_human_path(path: list[str]) -> str:
    path_ = path.copy()
    match path[0]:
        case "asset":
            pass
        case "asset.ability":
            path = path[-1:] + path[:-1]
        case "asset.ability.move":
            pass
        case "asset.ability.move.condition":
            pass
        case "asset.ability.move.outcome":
            pass
        case "asset.ability.oracle_rollable":
            pass
        case "asset.ability.oracle_rollable.row":
            pass
        case "asset_collection":
            pass
        case "atlas_collection":
            pass
        case "atlas_entry":
            pass
        case "delve_site":
            pass
        case "delve_site.denizen":
            pass
        case "delve_site_domain":
            pass
        case "delve_site_domain.danger":
            pass
        case "delve_site_domain.feature":
            pass
        case "delve_site_theme":
            pass
        case "delve_site_theme.danger":
            pass
        case "delve_site_theme.feature":
            pass
        case "move":
            pass
        case "move.condition":
            path = path[-1:] + path[:-1]
        case "move.oracle_rollable":
            pass
        case "move.oracle_rollable.row":
            pass
        case "move.outcome":
            pass
        case "move_category":
            pass
        case "npc":
            pass
        case "npc.variant":
            pass
        case "npc_collection":
            pass
        case "oracle_collection":
            pass
        case "oracle_rollable":
            path[0] = "oracle"
        case "oracle_rollable.row":
            pass
        case "rarity":
            pass
        case "truth":
            pass
        case "truth.option":
            path = path[-1:] + path[:-1]
        case "truth.option.oracle_rollable":
            path.pop(-2)
        case "truth.option.oracle_rollable.row        ":
            pass

        case _:
            log.warning(f"not treated: {path[0]}")
            # msg = f"Unknown type: {path[0]}"
            # raise ValueError(msg)
    p = " ".join(reversed(path))
    p = p.replace("_", " ").replace(".", " ")
    print(f"{path_} --> {p}")
    return p


def add_ruleset(rulesets: set[str]):
    play = rulesets - state["rulesets"]
    if not play:
        log.warning("Already playing: %s", ", ".join(state["rulesets"]))
        return
    state["rulesets"].update(play)
    idd = [get_id_tree(p)[p] for p in play]
    merged = depth_first_merge(*idd)
    paths = {}

    def _flatten_id_tree(tree: dict[str, Any], path: list[str] = []):
        for k, v in tree.items():
            if isinstance(v, dict):
                _flatten_id_tree(v, path + [k])
            else:
                p = build_human_path(path)
                paths[p] = v

    _flatten_id_tree(merged)
    state["paths"] |= paths

    # from rich.columns import Columns
    # print(Columns(sorted(paths)))


class InterpreterError(Exception):
    pass


class PragmaError(InterpreterError):
    pass


class Interpreter:
    def __init__(self):
        pass

    def interpret(self, statements: list[Expr] | None) -> list[Any]:
        if not statements:
            """Empty expression just prints some help."""
            if not state["rulesets"]:
                return [f"Try one of these: {' '.join(list(datasworn_tree))}"]

            return [f"Playing: {' '.join(list(state['rulesets']))}"]
        results: list[Any] = []
        try:
            for stmt in statements:
                result = self.visit(stmt)
                if result:
                    results.append(result)
        except Exception as e:
            log.error(e)
        return results

    def get_datasworn_object(self, name: str | None = None) -> Any:
        if name in datasworn_tree.keys():
            add_ruleset(set([name]))
            return datasworn_tree[name]

        paths = state.get("paths", None)
        if not paths:
            msg = "No references found. Did you say which ruleset(s) to play?"
            raise InterpreterError(msg)
        winner = fuzzy_search([name], state["paths"])
        if not winner:
            raise InterpreterError(f"Can't find reference: {name}")
        try:
            obj = datasworn_tree.index[winner]
        except KeyError:
            for i in datasworn_tree.index:
                print(i)
            raise InterpreterError(f"Unknown reference: {winner}")

        return obj

    def get_obj_from_expr(self, expr: list[Literal]) -> Any:
        obj = self.get_datasworn_object(expr[0].value)
        log.debug(f"{type(obj)} ({getattr(obj, 'id', None)})")

        return obj

    # VISITORS --------------------------------------------------------------

    @singledispatchmethod
    def visit(self, expr: Expr) -> Any:
        raise NotImplementedError

    @visit.register
    def _(self, stmt: ExprStmt) -> Any:
        """Expr without keyword just finds the referenced object."""
        log.debug(f"visit ExprStmt: {stmt}")
        obj = self.get_obj_from_expr(stmt.expr)
        # check for index
        if len(stmt.expr) > 1:
            obj = get_roller(obj, roll=int(stmt.expr[1].value))
            return obj
        return get_renderable(obj)

    @visit.register
    def _(self, stmt: KeywordStmt) -> Any:
        obj = self.get_obj_from_expr(stmt.expr)
        match stmt.token.value:
            case "print":
                return Pretty(
                    self.get_obj_from_expr(stmt.expr),
                    overflow="fold",
                    indent_guides=True,
                )

            case "roll":
                roller = get_roller(obj)

                return roller
            case _:
                raise InterpreterError(f"Unknown keyword: {stmt.name.value}")

    @visit.register
    def _(self, expr: DocString) -> Any:
        """Triple-quote delimited blocks are rendered as Markdown."""
        from rich.markdown import Markdown
        from rich.panel import Panel

        return Panel(
            Markdown(expr.text),
            border_style="scope.border",
        )
