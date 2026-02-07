from dataclasses import dataclass

from pysworn.repl.lexer import Token

"""
program: declaration* EOF
declaration: statement
statement: 
    | docstring
    | printStmt    
    | exprStmt
exprStmt: expression ";"
expression: literal (literal)*
literal:
    number
    symbol
    string    
"""


@dataclass
class Expr:
    token: Token


@dataclass
class Literal(Expr):
    value: int | str


@dataclass
class Stmt(Expr):
    pass


@dataclass
class DocString(Stmt):
    text: str


@dataclass
class ExprStmt(Stmt):
    expr: list[Literal]


@dataclass
class KeywordStmt(Stmt):
    expr: list[Literal]
