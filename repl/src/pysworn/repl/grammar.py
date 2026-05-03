from dataclasses import dataclass
from encodings.punycode import T

from pysworn.repl.lexer import Token

"""
program: declaration* EOF
declaration: varDeclaration | statement
varDeclaration: "new" identifier "=" expression ";"
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


# Expr ---------------------------------------------------------------------
class Expr:
    pass


@dataclass
class Assign(Expr):
    name: Token
    value: list[Expr]


@dataclass
class Identifier(Expr):
    value: str


@dataclass
class Symbol(Expr):
    value: str


@dataclass
class Variable(Expr):
    value: str


@dataclass
class Dice(Expr):
    value: str


@dataclass
class Number(Expr):
    value: str


# Stmt ---------------------------------------------------------------------
class Stmt:
    pass


@dataclass
class DocString(Stmt):
    value: str


@dataclass
class Expression(Stmt):
    expr: list[Expr]


@dataclass
class Command(Stmt):
    name: Token
    args: list[Expr]


@dataclass
class Builtin(Stmt):
    name: Token
    args: list[Expr]
