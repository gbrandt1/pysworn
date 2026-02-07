import logging
from dataclasses import dataclass
from re import L
from typing import Any

# token types
from pygments.token import (
    Keyword,
    Name,
    Number,
    Operator,
    String,
    _TokenType,  # pyright: ignore[reportPrivateUsage]
)

# grammar
from pysworn.repl.grammar import (
    DocString,
    Expr,
    ExprStmt,
    KeywordStmt,
    Literal,
    Stmt,
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
            log.info(stmt)
        return statements

    # UTILITIES ----------------------------------------------------------------

    def is_eof(self) -> bool:
        return self.peek().token_type is EndOfFile

    def advance(self) -> Token:
        if not self.is_eof():
            self.current += 1
        return self.previous()

    def match(self, *token_types: _TokenType):
        for token_type in token_types:
            if self.check(token_type):
                log.debug(f"match: {self.peek()}")
                self.advance()
                return True

        return False

    def check(self, token_type: _TokenType):
        if self.is_eof():
            return False
        return self.peek().token_type in token_type

    def peek(self) -> Token:
        # log.debug(f"Peeking: {self.tokens[self.current]}")
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
                Keyword.Reserved,
                String.Symbol,
                String.Doc,
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
        if self.match(Keyword):
            log.debug(f"Found Keyword: {self.previous().value}")
            return self.keyword_statement()

        if self.match(String.Doc):
            return self.docstring()

        return self.expression_statement()

    def keyword_statement(self) -> KeywordStmt:
        token = self.previous()
        expr = self.expression()
        self.consume(Operator.Semicolon, "Expected ';' after keyword statement.")
        return KeywordStmt(token, expr)

    def docstring(self) -> DocString:
        docs = DocString(self.previous(), self.previous().value[3:-3])
        self.consume(Operator.Semicolon, "Expected ';' after docstring.")
        return docs

    def expression_statement(self) -> ExprStmt:
        # log.debug("expression_statement")
        token = self.peek()
        expr = self.expression()
        self.consume(Operator.Semicolon, "Expected ';' after expression.")
        return ExprStmt(token, expr)

    # EXPRESSIONS --------------------------------------------------------------

    def expression(self) -> list[Any]:
        # log.debug("expression")
        expr: list[Any] = []
        while self.check(String) or self.check(Number):
            expr.append(self.primary())
        log.debug(f"expr={expr}")
        return expr

    def primary(self) -> Expr | None:
        log.debug(f"primary: '{self.peek().value}'")

        if self.match(String.Symbol, String, Number):
            return Literal(self.previous(), self.previous().value)

        self.error(self.peek(), "Expected literal.")
