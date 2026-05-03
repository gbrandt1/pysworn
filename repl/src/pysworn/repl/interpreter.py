import cmd
import fnmatch
import logging
from dataclasses import dataclass
from functools import singledispatchmethod
from typing import Any

from pysworn.common import Truths, datasworn_tree
from pysworn.renderables import get_renderable
from pysworn.repl.grammar import (
    # Builtin,
    Command,
    DocString,
    Expr,
    Expression,
)
from pysworn.repl.lexer import Token
from pysworn.repl.roller import get_roller
from pysworn.repl.state import state
from pysworn.repl.theme import pysworn_theme
from pysworn.repl.utils import (
    add_ruleset,
    fuzzy_search,
)
from rich.columns import Columns
from rich.console import Console
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text


@dataclass
class InterpreterError(Exception):
    token: Token
    message: str

    def __str__(self):
        return f"{self.token!r} {self.message}"


log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)

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
                log.debug(f"visit {stmt}")
                result = self.visit(stmt)
                if result:
                    results.append(result)
        except InterpreterError as exc:
            results.append(exc)
        except Exception as exc:
            results.append(exc)

        return results

    def get_datasworn_object(self, name: str) -> Any | None:
        log.debug(f"get_datasworn_object: {name}")
        paths = state.get("paths", None)
        if not paths:
            msg = "No references found. Did you say which ruleset(s) to play?"
            raise InterpreterError(name, msg)
        winner = fuzzy_search([name], state["paths"])
        if not isinstance(winner, str):
            return winner

        try:
            obj = datasworn_tree.index[winner]
        except KeyError:
            msg = f"Unknown reference: {winner}"
            raise ValueError(msg)

        return obj

    def get_obj_from_expr(self, name: str) -> Any:
        # token = expr[0].value
        # name = token.value

        # Special Ojects not reachable via Datasworn IDs

        if name == "rules":
            return datasworn_tree[state["rulesets"][0]].rules

        if name == "truths":
            truths = []
            for k, v in datasworn_tree.index.items():
                if k.startswith("truth:"):
                    truths.append(v)
            return Truths(truths)

        # Datasworn IDs starting with $

        if name.startswith("$"):
            pattern = f"{name[1:]}"
            ids = fnmatch.filter(datasworn_tree.index, pattern)
            if len(ids) != 1:
                log.debug(f"Found {len(ids)} matches")
                return Columns(Text.from_markup(i, style="log.path") for i in ids)
            else:
                obj = datasworn_tree.index[ids[0]]
        else:
            obj = self.get_datasworn_object(name)

        log.debug(f"{type(obj)} ({getattr(obj, 'id', None)})")
        return obj

    # VISITORS --------------------------------------------------------------

    @singledispatchmethod
    def visit(self, expr: Expr) -> Any:
        msg = f"visit not implemented for {type(expr)}"
        raise NotImplementedError(msg)

    @visit.register
    def _(self, stmt: Expression) -> Any | None:
        """Expr without keyword just finds the referenced object."""
        log.debug(f"visit Expression: {stmt}")

        name = " ".join(t.value.value for t in stmt.expr)
        # print(name)

        obj = self.get_obj_from_expr(name)
        renderable = get_renderable(obj)
        if renderable:
            return renderable
        return obj

    @visit.register
    def _(self, cmd: Command) -> Any:
        log.debug(f"visit Command: {cmd}")

        # name = cmd.name.value

        match cmd.name.value:
            case "load":
                name = " ".join(t.value.value for t in cmd.args)
                ruleset = datasworn_tree[name]
                add_ruleset(name)
                # print(state["paths"])
                return get_renderable(ruleset)

            case "index":
                return self.print_index(cmd)

            case "tree":
                return self.print_tree(cmd)

            case "paths":
                return self.print_paths(cmd)

        name = " ".join(t.value.value for t in cmd.args)
        obj = self.get_obj_from_expr(name)

        match cmd.name.value:
            case "print":
                return Pretty(
                    obj,
                    overflow="fold",
                    indent_guides=True,
                )

            case "roll":
                roller = get_roller(obj)
                log.debug(f"Roller: {type(roller)}")
                return roller

            case "set":
                return obj

            case _:
                raise InterpreterError(
                    cmd.token, f"Unimplemented keyword: {cmd.token.value}"
                )

    @visit.register
    def _(self, expr: DocString) -> Any:
        """Triple-quote delimited blocks are rendered as Markdown."""
        from rich.markdown import Markdown
        from rich.panel import Panel

        return Panel(
            Markdown(str(expr.value)),
            border_style="scope.border",
        )

    # Commands --------------------------------------------------------------

    def print_index(self, cmd: Command):
        # table = Table(show_header=False, border_style="scope.border", show_edge=False)
        for k in sorted(datasworn_tree.index):
            #     # id_ = datasworn_tree.index[k]
            #     table.add_row(
            #         # k,
            #         Text(k, style="log.path"),
            #     )
            # return table
            print(f"[green]${k}")

    def print_tree(self, cmd: Command):
        from rich.tree import Tree

        try:
            tree = state["tree"]
            if cmd.args:
                for v in cmd.args[0].value.split():
                    tree = tree[v]
        except KeyError:
            msg = f"Error in tree statement. {cmd.args}"
            raise InterpreterError(cmd.token, msg)

        rtree = Tree(
            " ".join(e.value for e in cmd.args),
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

    def print_paths(self, cmd: Command):

        table = Table(show_header=False, border_style="scope.border", show_edge=False)
        paths = sorted(state["paths"])
        pmax = max(len(p.split()) for p in paths)
        for k in paths:
            id_ = state["paths"][k]
            path = k.split()
            path_ = path[:-2] + ["·"] * (pmax - len(path))
            table.add_row(
                *path_,
                path[-2],
                path[-1],
                Text(id_, style="log.path"),
            )
        return table
