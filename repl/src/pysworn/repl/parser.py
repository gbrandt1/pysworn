import logging
from dataclasses import dataclass
from tkinter import W
from token import OP
from typing import Any

from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    String,
    Whitespace,
)
from pysworn.repl.expr import (
    # Assign,
    # Binary,
    Expr,
    # Unary,
    KeywordStmt,
    # Grouping,
    Literal,
    MarkdownBlock,
    Pragma,
    SequenceExpr,
)
from pysworn.repl.lexer import EndOfFile, Token
from rich import print

log = logging.getLogger(__name__)


@dataclass
class ParseException(Exception):
    """Exception raised for errors in the parsing process."""

    message: str
    line: int = -1
    col: int = -1

    def __str__(self) -> str:
        return f"{self.message}"


@dataclass
class ParseError(Exception):
    token: Token
    message: str


class Parser:
    def __init__(self, tokens: list[Any]) -> None:
        self.tokens: list[Any] = tokens
        self._current = 0

    def parse(self) -> list[Expr] | None:
        """Parse the list of tokens and return the corresponding AST."""

        # statements: list[Expr] = []
        # while not self._is_eof():
        #     statements.append(self._declaration())
        # return statements

        # try:
        statements: list[Expr] = []
        while not self._is_eof():
            stmt = self._statement()
            statements.append(stmt)
            log.info(stmt)

        # except ParseException:
        #     return None
        return statements

    def _is_eof(self) -> bool:
        return self._peek().token_type in EndOfFile

    def _advance(self) -> Token:
        """Return the next token to be consumed by the parser & advance the pointer location."""
        log.debug(f"_advance_: {self._peek()}")
        if not self._is_eof():
            self._current += 1
        return self._previous()

    def _match(self, *query_token_types: type) -> bool:
        """Check if the current token matches any of the query token type(s)."""

        log.debug(f"Matching {query_token_types} against {self._peek()}")

        if any((self._check(query_token) for query_token in query_token_types)):
            self._advance()
            return True

        return False

    def _check(self, query_token_type: type) -> bool:
        """Check if the current token matches the query token type."""
        if self._is_eof():
            return False
        # log.debug(f"Checking {self._peek().token_type} against {query_token_type}")
        return self._peek().token_type is query_token_type

    def _peek(self) -> type:
        """Return the current token we have yet to consume."""
        return self.tokens[self._current]

    def _previous(self) -> Token:
        """Return the most recently consumed token."""
        return self.tokens[self._current - 1]

    def _consume(self, query_token_type, msg: str) -> Token:
        """
        Check if the current token matches the query token type.

        If the current token is a match, the token is consumed & retured. Otherwise, an error is
        raised with the provided error message & a `ParseException` returned to assist with
        synchronization.
        """
        if not self._check(query_token_type):
            self._report_error(ParseError(self._peek(), msg))

        return self._advance()

    def _report_error(self, err: ParseError) -> ParseException:
        """Report the provided error to the invoking interpreter & return an exception for sync."""
        # self._interpreter.report_error(err)

        msg = f"{err.token!r} {err.message}"
        raise ParseException(msg)

    def _synchronize(self) -> None:
        self._advance()

        while not self._is_eof():
            if self._previous().token_type == Operator.Semicolon:
                return

            match self._peek().token_type:
                # case Whitespace:
                #     self._advance()
                # case Comment:
                #     self._advance()
                case _:
                    return

            self._advance()

    def _declaration(self) -> Any:
        try:
            return self._statement()
        except ParseException:
            self._synchronize()

    def _statement(self):
        if self._match(String.Markdown):
            log.debug("Found Markdown:")
            md = self._previous().value[3:-3]  # strip markdown delimiters
            return MarkdownBlock(md)

        if self._match(Keyword.Pragma):
            log.debug(f"Found Pragma: {self._previous().value}")
            pragma = self._previous().value

            if self._match(Name.Sequence, Number):
                log.debug(f"Found Value: {self._previous().value}")
                value = self._previous().value
            else:
                value = None
            self._consume(Operator.Semicolon, "Expected ';' after pragma.")
            return Pragma(pragma, value)

        if self._match(Keyword):
            log.debug(f"Found Keyword: {self._previous().value}")
            keyword = self._previous().value

            if self._match(Name.Sequence, Number):
                log.debug(f"Found Value: {self._previous().value}")
                value = self._previous().value

            self._consume(Operator.Semicolon, "Expected ';' after keyword.")
            return KeywordStmt(keyword, value)

        return self._expression_statement()

    def _expression_statement(self) -> Expr:
        expr = self._expression()

        while self._match(Name):
            values
        self._consume(Operator.Semicolon, "Expected ';' after value.")
        return expr

    def _expression(self) -> Expr:
        return self._unary()

    def _unary(self) -> Expr:
        """
        Parse the unary grammar.

        `unary: ( "!" | "-" ) unary | call`
        """
        if self._match(Operator.Minus, Operator.Plus):
            operator = self._previous()
            right = self._unary()

            return Unary(operator, right)

        return self._primary()

    def _primary(self) -> Expr:
        """
        Parse the primary grammar.

        ```
        primary:
            | NUMBER
            | STRING
            | IDENTIFIER
            | "(" expression ")"
        ```
        """

        if self._match(Number):
            log.debug(f"Found Number: {self._previous().value}")
            return Literal(self._previous().value)

        if self._match(String):
            log.debug(f"Found String: {self._previous().value}")
            return Literal(self._previous().value)

        # if self._match(Operator.LParen):
        #     expr = self._expression()
        #     self._consume(Operator.RParen, "Expected ')' after expression.")
        #     return Grouping(expr)

        if self._match(Name.Sequence):
            return SequenceExpr(self._previous())

        self._report_error(ParseError(self._peek(), "Expected expression."))


if __name__ == "__main__":
    from rich.logging import RichHandler

    FORMAT = "%(message)s"

    logging.basicConfig(
        level="DEBUG",
        format=FORMAT,
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )

    logging.getLogger("markdown_it").setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG)

    from pysworn.repl.lexer import lexer

    text = ""
    with open("example.sworn", "r") as f:
        text = f.read()
    lexer.tokenize(text)
    tokens = lexer.clean_tokens()

    # clean up before parsing

    # print("Cleaned tokens:")
    # for t in tokens:
    #     print(t)

    # convert to Token dataclass
    # tokens = [PyswornToken(token_type=t[0], lexeme=t[1]) for t in tokens]

    parser = Parser(tokens)
    ast = parser.parse()
    print(ast)
