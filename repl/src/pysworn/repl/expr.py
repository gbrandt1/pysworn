from dataclasses import dataclass
from typing import Sequence

from pysworn.repl.lexer import Token

"""
program --> declaration* EOF
declaration --> varDecl | statement
varDecl --> IDENTIFIER (":=" expression)?
statement --> exprStmt | markdown | pragma EOL
markdown --> MARKDOWN
pragma --> PRAGMA IDENTIFIER (":" IDENTIFIER)*
"""


@dataclass
class Expr:
    pass


@dataclass
class Pragma(Expr):
    name: Token
    values: SequenceExpr


@dataclass
class MarkdownBlock(Expr):
    text: str


# @dataclass(slots=True, eq=False)
# class Assign(Expr):
#     name: Token
#     value: Expr


# @dataclass
# class Binary(Expr):
#     left: Expr
#     operator: Token
#     right: Expr


# @dataclass
# class Grouping(Expr):
#     expression: Expr


@dataclass
class Literal(Expr):
    value: int | str


# @dataclass
# class Unary(Expr):
#     operator: Token
#     right: Expr


@dataclass
class SequenceExpr(Expr):
    name: Token


@dataclass
class Stmt:
    pass


@dataclass
class ExprStmt(Stmt):
    expr: Expr


@dataclass
class KeywordStmt(Stmt):
    name: Token
    value: SequenceExpr
