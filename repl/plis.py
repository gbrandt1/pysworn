"""plis.py

https://gitlab.com/carlbordum/plis.py/-/blob/main/plis.py

plis.py is a re-implementation of Peter Norvig's legendary lis.py using Python
3.10's new structural pattern matching.

Peter Norvig's "(How to Write a (Lisp) Interpreter (in Python))":
    http://norvig.com/lispy.html
Structural Pattern Matching:
    PEP 634 -- Specification: https://www.python.org/dev/peps/pep-0634/
    PEP 635 -- Motivation and Rationale: https://www.python.org/dev/peps/pep-0635/
    PEP 636 -- Tutorial: https://www.python.org/dev/peps/pep-0636/
"""

import math
import operator
from collections import ChainMap
from dataclasses import dataclass
from functools import reduce
from typing import Any, MutableMapping


class Paren:
    L, R = range(2)


@dataclass
class Number:
    value: int


@dataclass(frozen=True)
class Symbol:
    value: str


Token = Paren | Number | Symbol
TokenList = list[Token]
AST = Token | list["AST"]
Env = MutableMapping[Symbol, Any]


@dataclass
class Procedure:
    params: list[Symbol]
    body: AST
    env: Env

    def __call__(self, *args: AST):
        local_env = dict(zip(self.params, args))
        return eval(self.body, ChainMap(local_env, self.env))


def tokenize(program: str) -> TokenList:
    """Tokenize a plis.py program."""
    for token_str in program.replace("(", " ( ").replace(")", " ) ").split():
        match token_str:
            case "(":
                yield Paren.L
            case ")":
                yield Paren.R
            case n if n.isdigit():
                yield Number(int(n))
            case symbol:
                yield Symbol(symbol)


def parse(tokens: TokenList) -> AST:
    """Convert a tokenized program to an AST."""
    match next(tokens):
        case Paren.L:
            scope = []
            while (r := parse(tokens)) != Paren.R:
                scope.append(r)
            return scope
        case token:
            return token


def standard_env() -> Env:
    """Return an environment with built-in procedures."""
    return {
        Symbol(k): v
        for k, v in {
            "*": lambda *numbers: reduce(operator.mul, numbers),
            "+": lambda *numbers: sum(numbers),
            "-": lambda *numbers: reduce(operator.sub, numbers),
            "/": lambda *numbers: reduce(operator.truediv, numbers),
            "<": operator.lt,
            "<=": operator.le,
            "=": operator.eq,
            ">": operator.gt,
            ">=": operator.ge,
            "abs": abs,
            "append": operator.add,
            "apply": lambda proc, args: proc(*args),
            "begin": lambda *x: x[-1],
            "car": lambda x: x[0],
            "cdr": lambda x: x[1:],
            "cons": lambda x, y: [x] + y,
            "equal?": operator.eq,
            "expt": pow,
            "length": len,
            "list": lambda *x: list(x),
            "map": lambda f, x: list(map(f, x)),
            "max": max,
            "min": min,
            "not": operator.not_,
            "null?": lambda x: x == [],
            "number?": lambda x: isinstance(x, int),
            "pi": math.pi,
            "pow": math.pow,
            "print": print,
            "procedure?": callable,
            "symbol?": lambda x: isinstance(x, Symbol),
        }.items()
    }


def eval(expression: AST, env: Env):
    """Evaluate an AST with respect to env."""
    match expression:
        case [Symbol(value="if"), test, consequence, alternative]:
            result = eval(test, env)
            branch = consequence if result else alternative
            return eval(branch, env)
        case [Symbol(value="define"), Symbol() as key, expr]:
            env[key] = eval(expr, env)
        case [Symbol(value="quote"), expr]:
            return expr
        case [Symbol(value="lambda"), params, body]:
            return Procedure(params, body, env)
        case Symbol() as key:
            return env[key]
        case Number(value=n):
            return n
        case [Symbol() as f, *args]:
            function = env[f]
            evaluated_args = [eval(expr, env) for expr in args]
            return function(*evaluated_args)
        case [Procedure() as proc, *args]:
            return proc(*args)
        case [*expression]:
            return eval([eval(expr, env) for expr in expression], env)


def repl():
    env = standard_env()
    while True:
        line = input("plis.py> ")
        result = eval(parse(tokenize(line)), env)
        if result is not None:
            print(result)


if __name__ == "__main__":
    repl()
