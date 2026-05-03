import logging
from dataclasses import dataclass
from typing import Any

# token types
from pygments.token import (
    Keyword,
    Literal,
    Name,
    Operator,
    String,
    _TokenType,  # pyright: ignore[reportPrivateUsage]
)

# grammar
from pysworn.repl.grammar import (
    Builtin,
    Command,
    Dice,
    DocString,
    Expr,
    Expression,
    Identifier,
    Number,
    Stmt,
    Symbol,
    Variable,
)
from pysworn.repl.lexer import EndOfFile, Token

log = logging.getLogger(__name__)


@dataclass
class ParseError(Exception):
    token: Token
    message: str


class Parser:
    def __init__(self, tokens: list[Any], error_handler: Any = None) -> None:
        self.tokens: list[Any] = tokens
        self.error_handler = error_handler
        self.current = 0

    def parse(self) -> list[Expr] | None:
        statements: list[Expr] = []
        while not self.is_eof():
            stmt = self.declaration()
            statements.append(stmt)
            log.debug(stmt)
        return statements

    # UTILITIES ----------------------------------------------------------------

    def is_eof(self) -> bool:
        return self.peek().token_type is EndOfFile

    def advance(self) -> Token:
        if not self.is_eof():
            self.current += 1
        return self.previous()

    def match(self, *token_types):
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def check(self, token_type):
        if self.is_eof():
            return False
        return self.peek().token_type in token_type

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def consume(self, token_type: _TokenType, msg: str):
        if not self.check(token_type):
            self.error(self.peek(), msg)

        return self.advance()

    def error(self, token: Token, msg: str):
        self.error_handler.error(token, msg)
        return ParseError

    def synchronize(self) -> None:
        """Recover from error to continue parsing."""
        self.advance()

        while not self.is_eof():
            if self.previous().token_type == Operator.Semicolon:
                return

            if self.peek().token_type in (
                Keyword,
                String,
                Name,
            ):
                return

            self.advance()

    # DECLARATIONS ------------------------------------------------------------

    def declaration(self) -> Any:
        try:
            return self.statement()
        except ParseError:
            self.synchronize()
            return None

    # STATEMENTS ---------------------------------------------------------------

    def statement(self) -> Stmt:
        if self.match(Name.Builtin):
            return self.builtin_statement()

        if self.match(Keyword):
            return self.keyword_statement()

        if self.match(String.Doc):
            return self.docstring_statement()

        return self.expression_statement()

    def builtin_statement(self) -> Builtin:
        name = self.previous()
        expr = self.expression()
        self.consume(Operator.Semicolon, "Expected ';' after builtin statement.")
        return Builtin(name, expr)

    def keyword_statement(self) -> Command:
        name = self.previous()
        expr = self.expression()
        self.consume(Operator.Semicolon, "Expected ';' after keyword statement.")
        return Command(name, expr)

    def docstring_statement(self) -> DocString:
        docs = DocString(self.previous().value[3:-3])
        self.consume(Operator.Semicolon, "Expected ';' after docstring.")
        return docs

    def expression_statement(self) -> Expression:
        expr = self.expression()
        log.debug(f"expression_statement: {expr}")
        self.consume(Operator.Semicolon, "Expected ';' after value.")
        return Expression(expr)

    # EXPRESSIONS --------------------------------------------------------------

    def expression(self) -> list[Any]:
        return self.assignment()

    def assignment(self) -> list[Any]:
        expr: list[Any] = []
        while self.check(Name) or self.check(String) or self.check(Literal):
            expr.append(self.primary())
            log.debug(f"expr={expr}")
            # self.match(Operator.Colon):
            # return expr

        return expr

    def primary(self) -> Expr | None:
        log.debug(f"primary: '{self.peek().value}'")

        if self.match(String.Doc):
            return DocString(self.previous())

        if self.match(String.Identifier):
            return Identifier(self.previous())

        if self.match(String.Symbol):
            return Symbol(self.previous())

        if self.match(Name.Variable):
            return Variable(self.previous())

        if self.match(String.Dice):
            return Dice(self.previous())

        if self.match(Literal.Number):
            return Number(self.previous())

        self.error(self.peek(), "Expected literal.")
