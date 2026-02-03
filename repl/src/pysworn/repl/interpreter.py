import logging
import random
from functools import singledispatchmethod
from typing import Any

from pysworn.common import datasworn_tree
from pysworn.renderables import get_renderable
from rich import print

from pysworn.repl.expr import (
    Expr,
    KeywordStmt,
    MarkdownBlock,
    Pragma,
    SequenceExpr,
)
from pysworn.repl.roller import get_roller
from pysworn.repl.utils import depth_first_merge, fuzzy_search, get_id_dict

log = logging.getLogger(__name__)

# global interpreter state
state = {}


class InterpreterError(Exception):
    pass


class PragmaError(InterpreterError):
    pass


class Interpreter:
    def __init__(self):
        pass

    def interpret(self, statements: list[Expr]) -> list[Any]:
        results: list[Any] = []
        try:
            for stmt in statements:
                result = self.visit(stmt)
                if result:
                    results.append(result)
        except Exception as e:
            log.error(e)
        return results

    def get_reference_object(self, name: str):
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
            raise InterpreterError(f"Unknown reference: {winner}")
        return obj

    @singledispatchmethod
    def visit(self, expr: Expr) -> Any:
        raise NotImplementedError

    @visit.register
    def _(self, expr: SequenceExpr) -> Any:
        """SequenceExpr without keyword just prints the reference object."""
        obj = self.get_reference_object(expr.name.value)
        renderable = get_renderable(obj)
        if renderable:
            return renderable
        log.error(f"No renderable for {type(obj)}")
        return obj

    @visit.register
    def _(self, stmt: KeywordStmt) -> Any:
        log.debug(stmt.name)
        match stmt.name:
            case "print":
                return self.get_reference_object(stmt.value)

            case "roll":
                # print(stmt)
                obj = self.get_reference_object(stmt.value)
                # print(obj)
                roller = get_roller(obj)
                return roller
            case _:
                raise InterpreterError(f"Unknown keyword: {stmt.name.value}")

    @visit.register
    def _(self, expr: MarkdownBlock) -> Any:
        """Triple-quote delimited blocks are just rendered as Markdown."""
        from rich.markdown import Markdown
        from rich.panel import Panel

        return Panel(Markdown(expr.text))

    @visit.register
    def _(self, expr: Pragma) -> Any:
        """Pragmas set the configuration of the interpreter."""
        log.debug(expr)
        match expr.name:
            case "seed":
                random.seed(expr.values[0])
                log.info(
                    f"Random seed set to {expr.values[0]} --> {random.randint(1, 100)}"
                )

            case "play":
                if not expr.values:
                    print(f"Playing {' '.join(state['rulesets'])}")
                # TODO: use _MatchBreak exception
                else:
                    play = expr.values.split(" ")
                    state["rulesets"] = play
                    for p in play:
                        # trigger lazy-loading
                        datasworn_tree[p]

                    # nested id dicts for each ruleset
                    idd = [get_id_dict(p, exclude=".")[p] for p in play]
                    # print(idd)
                    # merged nested id dicts
                    merged = depth_first_merge(*idd)
                    # print(merged)
                    paths = {}

                    # flatten id dict
                    def _flatten(d: dict[str, Any], path: str = ""):
                        for k, v in d.items():
                            path_ = f"{k} {path}"
                            if isinstance(v, dict):
                                _flatten(v, path_)
                            else:
                                path_ = (
                                    path_.strip()
                                    .replace("_rollable", "")
                                    .replace("_", " ")
                                )
                                paths[path_] = v

                    _flatten(merged)
                    # print(paths)
                    state["paths"] = paths

            case "match":
                # log.info(f"Matching set to {expr.values}")
                pass
            case _:
                raise PragmaError(expr.name, f"Unknown pragma: {expr.name.value}")
