import fnmatch
import logging
from dataclasses import dataclass
from functools import singledispatchmethod
from typing import Any

from pysworn.common import datasworn_tree
from pysworn.renderables import get_renderable
from pysworn.repl.grammar import (
    DocString,
    Expr,
    ExprStmt,
    KeywordStmt,
    Literal,
)
from pysworn.repl.lexer import Token
from pysworn.repl.roller import get_roller
from pysworn.repl.state import state
from pysworn.repl.theme import pysworn_theme
from pysworn.repl.utils import (
    add_ruleset,
    fuzzy_search,
)
from pysworn.common import Truths
from rich.console import Console
from rich.pretty import Pretty


@dataclass
class InterpreterError(Exception):
    token: Token
    message: str

    def __str__(self):
        return f"{self.token!r} {self.message}"


log = logging.getLogger(__name__)


console = Console(theme=pysworn_theme)

print = console.print


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
        except InterpreterError as e:
            log.error(e)
        # except ValueError as e:
        # log.error(e)
        except Exception as e:
            log.exception(e)

        return results

    def get_datasworn_object(self, stmt: ExprStmt) -> Any | None:

        name = stmt[0].value
        if name in datasworn_tree.keys():
            add_ruleset(name)
            return datasworn_tree[name]

        paths = state.get("paths", None)
        if not paths:
            msg = "No references found. Did you say which ruleset(s) to play?"
            raise InterpreterError(stmt[0].token, msg)
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
        name = expr[0].value        
        # truths
        if name == "truths":
            truths = []
            for k, v in datasworn_tree.index.items():
                if k.startswith("truth:"):
                    truths.append(v)
            return Truths(truths)

        # identifiers starting with $
        if name.startswith('$'):
            pattern = f"{name[1:]}"
            ids = fnmatch.filter(datasworn_tree.index, pattern)
            if len(ids) != 1:
                for i in ids:
                    print(f"[green]{i}")
                return
            else:
                obj = datasworn_tree.index[ids[0]]
        else:
            obj = self.get_datasworn_object(expr)
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
            obj = get_roller(obj, roll=stmt.expr[1].value)
            return obj
        
        return get_renderable(obj)

    @visit.register
    def _(self, stmt: KeywordStmt) -> Any:
        match stmt.token.value:
            case "print":                
                return Pretty(
                    self.get_obj_from_expr(stmt.expr),
                    overflow="fold",
                    indent_guides=True,
                )

            case "roll":
                obj = self.get_obj_from_expr(stmt.expr)
                roller = get_roller(obj)
                log.debug(f"Roller: {type(roller)}")
                return roller

            case "tree":
                return self.print_tree(stmt)
 
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

    # Commands --------------------------------------------------------------

    def print_tree(self, stmt: ExprStmt):
        from rich.tree import Tree

        try:
            tree = state["tree"]
            if stmt.expr:
                for v in stmt.expr[0].value.split():
                    tree = tree[v]
        except KeyError:
            msg = f"Error in tree statement. {stmt.expr}"
            raise InterpreterError(stmt.token, msg)

        rtree = Tree(
            " ".join(e.value for e in stmt.expr),
            guide_style="scope.border",
        )

        def _recurse_tree(node: Tree, tree: dict[str, Any]):
            for k, v in tree.items():
                if isinstance(v, dict):
                    if len(v) > 1:
                        subnode = node.add(f"{k}")
                        _recurse_tree(subnode, v)
                    if "id" in v and len(v) == 1:
                        node.add(f"{k} [blue]{v['id']}[/]")

        _recurse_tree(rtree, tree)
        return rtree
