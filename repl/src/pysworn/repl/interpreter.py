import logging
from ast import Call
from dataclasses import dataclass
from functools import singledispatchmethod
from re import M
from typing import Any, Callable

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
from pysworn.repl.lexer import EndOfFile, Token
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


@dataclass
class InterpreterError(Exception):
    token: Token
    message: str


log = logging.getLogger(__name__)


console = Console(theme=pysworn_theme)

print = console.print

# global interpreter state
state: dict[str, Any] = {
    "rulesets": set(),  # TODO: needs to be list to keep preference order
    "paths": {},
}


def build_human_path(path: list[str]) -> str | None:
    """Transform id path to human typeable path"""

    path_dd: dict[str, Callable[[list[str]], Any]] = {
        # ASSETS
        "asset": lambda p: p,
        "asset.ability": lambda p: None,  # rollable
        "asset.ability.move": lambda p: ["move"] + p[1:-2] + p[-1:],
        "asset.ability.move.condition": lambda p: None,  # TODO: extract options from move
        "asset.ability.move.outcome": lambda p: ["move"] + p[1:-3] + p[-2:],
        "asset.ability.oracle_rollable": lambda p: ["oracle"] + p[1:-2] + p[-1:],
        "asset.ability.oracle_rollable.row": lambda p: None,  # rollable
        "asset_collection": lambda p: ["assets"] + p[1:],
        # ATLAS
        "atlas_collection": lambda p: p,
        "atlas_entry": lambda p: p,
        # DELVE
        "delve_site": lambda p: p,
        "delve_site.denizen": lambda p: p,
        "delve_site_domain": lambda p: p,
        "delve_site_domain.danger": lambda p: p,
        "delve_site_domain.feature": lambda p: p,
        "delve_site_theme": lambda p: p,
        "delve_site_theme.danger": lambda p: p,
        "delve_site_theme.feature": lambda p: p,
        # MOVES
        "move": lambda p: p,
        "move.condition": lambda p: None,  # TODO: extract options from move
        "move.oracle_rollable": lambda p: ["oracle", "move"] + p[1:],
        "move.oracle_rollable.row": lambda p: None,  # rollable
        "move.outcome": lambda p: ["move"] + p[1:],
        "move_category": lambda p: ["moves"] + p[1:],
        "npc": lambda p: p,
        "npc.variant": lambda p: ["npc"] + p[1:-2] + p[-1:],
        "npc_collection": lambda p: ["npcs"] + p[1:],
        "oracle_collection": lambda p: ["oracles"] + p[1:],
        "oracle_rollable": lambda p: ["oracle"] + p[1:],
        "oracle_rollable.row": lambda p: None,  # rollable
        "rarity": lambda p: p,
        "truth": lambda p: p,
        "truth.option": lambda p: None,  # rollable
        "truth.option.oracle_rollable": lambda p: ["oracle"] + p[1:-2] + p[-1:],
        "truth.option.oracle_rollable.row": lambda p: None,  # rollable
    }
    try:
        path_ = path_dd[path[0]](path)
    except KeyError:
        msg = f"Unknown type: {path[0]}"
        raise ValueError(msg)
    if not path_:
        return None
    p = [p.capitalize() for p in path_]
    p = " ".join(reversed(p))
    p = p.replace("_", " ").replace(".", " ")
    log.debug(f"{path} --> {p}")
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
                if p := build_human_path(path):
                    if v in paths:
                        msg = f"Duplicate path: {v}"
                        raise ValueError(msg)
                    paths[p] = v

    _flatten_id_tree(merged)
    state["paths"] |= paths

    # from rich.columns import Columns
    # print(Columns(sorted(paths)))


class Interpreter:
    def __init__(self):
        pass

    def interpret(self, stmts: list[Expr] | None) -> list[Any]:
        if not stmts:
            """Empty expression just prints some help."""
            if not state["rulesets"]:
                return [f"Try one of these: {' '.join(list(datasworn_tree))}"]

            return [f"Playing: {' '.join(list(state['rulesets']))}"]
        results: list[Any] = []
        try:
            for stmt in stmts:
                result = self.visit(stmt)
                if result:
                    results.append(result)
        except Exception as e:
            log.exception(e)
        return results

    def get_datasworn_object(self, name: str) -> Any | None:
        if name in datasworn_tree.keys():
            add_ruleset(set([name]))
            return datasworn_tree[name]

        paths = state.get("paths", None)
        if not paths:
            msg = "No references found. Did you say which ruleset(s) to play?"
            raise ValueError(msg)
        winner = fuzzy_search([name], state["paths"])
        if not winner:
            return
        try:
            obj = datasworn_tree.index[winner]
        except KeyError:
            for i in datasworn_tree.index:
                print(i)
            raise ValueError(f"Unknown reference: {winner}")

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
    def _(self, stmt: ExprStmt) -> Any | None:
        """Expr without keyword just finds the referenced object."""
        log.debug(f"visit ExprStmt: {stmt}")
        obj = self.get_obj_from_expr(stmt.expr)
        if not obj:
            return
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

            # case "suffer":

            case _:
                raise InterpreterError(
                    stmt.token, f"Unimplemented keyword: {stmt.token.value}"
                )

    @visit.register
    def _(self, expr: DocString) -> Any:
        """Triple-quote delimited blocks are rendered as Markdown."""
        from rich.markdown import Markdown
        from rich.panel import Panel

        return Panel(
            Markdown(expr.text),
            border_style="scope.border",
        )
