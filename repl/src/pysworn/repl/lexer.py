"""
Regex-based lexer for Sworn script language.

The lexer reuses Pygments token types and state defintion
for direct integration with Pygments.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

from pygments.lexer import RegexLexer
from pygments.token import (
    Comment,
    Generic,
    Keyword,
    Name,
    Number,
    Operator,
    String,
    Whitespace,
    _TokenType,
)
from pysworn.repl.tokens import KEYWORDS, RULESETS
from rich import print
from rich.console import Console, ConsoleOptions, RenderResult
from rich.syntax import Syntax

log = logging.getLogger(__name__)


@dataclass
class Token:
    token_type: _TokenType
    value: str
    pos: int
    line: int
    col: int

    def __rich__(self) -> str:
        return f"{self.line:>3}:{self.col:>2} <{self.token_type!r} {self.value!r}>"

    def __repr__(self) -> str:
        return f"Token({self.token_type!r}, {self.value!r}, {self.pos!r}, {self.line!r}, {self.col!r})"


triple_quoted_string = (
    r'("""(?:[^"\\]|\\.|"(?="))*"""|\'\'\'(?:[^\'\\]|\\.|\'(?=\'\'))*\'\'\')'
)
double_quoted_string = r'"(?:\\.|[^"\\n])*"'
single_quoted_string = r"'([^'\\]*(?:\\.[^'\\]*)*)'"


BUILTINS = RULESETS


keywords_regex = r"\b(" + "|".join(KEYWORDS) + r")\b"
# builtins_regex = r"\b(" + "|".join(BUILTINS) + r")\b"
identifier_regex = r"\$[a-z0-9\_:/\.\*]*$"

state = [
    (r"--.*$", Comment),
    (triple_quoted_string, String.Doc),
    (double_quoted_string, String.Double),
    (single_quoted_string, String.Single),
    (keywords_regex, Keyword),
    # (builtins_regex, Name.Builtin),
    (identifier_regex, String.Identifier),
    # (r"[a-zA-Z_]+([ ]+([a-zA-Z_])+)*", String.Symbol),
    (r"[a-zA-Z][a-zA-Z0-9\-\_]*", Name.Variable),
    (r"\d+d\d+", String.Dice),
    (r"\d+", Number),
    # (r"=", Operator.Assignment),
    (r"\.", Operator.Dot),
    # (r"\+", Operator.Plus),
    # (r"-", Operator.Minus),
    # (r"\*", "MULTIPLY"),
    # (r"/", "DIVIDE"),
    # (r"\(", Operator.LParen),
    # (r"\)", Operator.RParen),
    # (r"=", Operator.Equal),
    # (r":", Operator.Colon),
    (r";", Operator.Semicolon),
    (r"\n", Generic.Newline),
    # (r"^[ \t]+\b", Whitespace.Indent),  # Leading whitespace
    (r"[ \t]+", Whitespace),  # Ignore whitespace
]


EndOfFile = Generic.EndOfFile


class PygmentsSwornLexer(RegexLexer):
    """Pygments Lexer for Sworn script language."""

    name = "Sworn"
    url = "https://github.com/gbrandt1/pysworn"
    aliases = ["sworn"]
    filenames = ["*.sworn", "*.pysworn"]
    tokens = {"root": state}


class ScanError(Exception):
    def __init__(self, line: int, col: int, message: str | None = None):
        self.message = message
        self.line = line - 1
        self.col = col

    def __rich__(self):
        return f"[red]{self.message}\n{' ' * self.col}^"


class Lexer:
    """Lexer for Sworn script language."""

    def __init__(self, src: str, rules: list[tuple[str, _TokenType]] = state) -> None:
        self.text = src
        self.rules = rules
        self.tokens: list[Token] = []
        self.errors: list[Exception] = []

        # Compile regex patterns with named groups
        regex_parts: list[str] = []
        self.group_type: dict[str, Any] = {}
        for idx, (regex, token_type) in enumerate(rules):
            groupname = f"GROUP{idx}"
            regex_parts.append(f"(?P<{groupname}>{regex})")
            self.group_type[groupname] = token_type
        self.regex = re.compile("|".join(regex_parts), re.MULTILINE)

    def tokenize_unprocessed(self) -> list[Token]:
        """Tokenize a string into a list Tokens."""

        pos = 0
        line = 1
        col = 0

        while pos < len(self.text):
            match = self.regex.match(self.text, pos)

            if not match:
                msg = f"[{line}] Unexpected character"
                raise ScanError(line, col, f"{msg}\n{self.text.split('\n')[line - 1]}")

            groupname = match.lastgroup
            if not groupname:
                msg = f"[{line}] Unexpected group"
                raise ScanError(line, col, f"{msg}\n{self.text.split('\n')[line - 1]}")

            token_type = self.group_type[groupname]
            value = match.group(groupname)
            if token_type == Generic.Newline:
                line += 1
                col = 0
            if token_type == String.Doc:
                line += value.count("\n")
            col += len(value)
            self.tokens.append(
                Token(
                    token_type=token_type,
                    value=value,
                    pos=pos,
                    line=line,
                    col=col,
                )
            )
            pos = match.end()

        self.tokens.append(Token(EndOfFile, "", pos + 1, line, col + 1))
        return self.tokens

    def tokenize(self) -> list[Token]:
        """
        - Remove comments and whitespace.
        - Insert semicolons.
        - Merge semicolons and newlines.
        """

        tokens_: list[Token] = []

        line = ""
        for t in self.tokens:
            if t.token_type is Comment:
                continue

            if t.token_type is Whitespace:
                continue

            if t.token_type is Generic.Newline:
                if len(line) > 0 and line[-1] != ";":
                    t.token_type = Operator.Semicolon
                    t.value = ";"
                    tokens_.append(t)
                line = ""
                continue

            tokens_.append(t)
            line += t.value

        return tokens_

    def scan_tokens(self):
        try:
            self.tokenize_unprocessed()
        except ScanError as e:
            self.errors.append(e)
        try:
            return self.tokenize()
        except Exception as e:
            self.errors.append(e)

    def untokenize(self) -> Syntax:
        untokenized = ""
        for token in self.tokens:
            untokenized += token.value

        syntax = Syntax(
            untokenized, PygmentsSwornLexer(), theme="pysworn", line_numbers=True
        )
        return syntax

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield "Lexer Output:"
        for token in self.tokenize():
            if token.token_type is Operator.Semicolon:
                yield f"{token.line:>3}:{token.col:>2} ;"
            else:
                yield token


if __name__ == "__main__":
    import sys
    from pathlib import Path

    path = Path(sys.argv[1])
    with path.open("rt") as file:
        src = file.read()

        lexer = PygmentsSwornLexer()
        for pos, token, lexeme in lexer.get_tokens_unprocessed(src):
            print(f"{pos:4} {token} {lexeme!r}")
