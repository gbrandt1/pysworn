"""
Lexer for Sworn script language.

The lexer reuses Pygments tokens and state defintion
for direct integration with Pygments.
"""

import logging
import re
from dataclasses import dataclass
from tkinter import W
from typing import Any

import rich.repr
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
)
from pygments.token import (
    Token as PygmentsToken,
)
from rich import print
from rich.syntax import Syntax

log = logging.getLogger(__name__)

# TODO: use Pygments bygroups()
triple_quoted_string = (
    r'("""(?:[^"\\]|\\.|"(?="))*"""|\'\'\'(?:[^\'\\]|\\.|\'(?=\'\'))*\'\'\')'
)
double_quoted_string = r'"(?:\\.|[^"\\n])*"'
single_quoted_string = r"'([^'\\]*(?:\\.[^'\\]*)*)'"

# TODO: use Pygments words()
pragmas = ["match", "play", "seed"]
keywords = [
    "roll",
    "take",
    "mark",
    # "progress roll",
    # "action roll",
    "burn",
    "in control",
    "in bad spot",
    "reset",
    "suffer",
    "from",
]
pragmas_regex = r"\b(" + "|".join(pragmas) + r")\b"
keywords_regex = r"\b(" + "|".join(keywords) + r")\b"

state = [
    (r"--.*", Comment),
    (triple_quoted_string, String.Doc),
    (double_quoted_string, String.Double),
    (single_quoted_string, String.Single),
    (pragmas_regex, Keyword.Reserved),
    (keywords_regex, Keyword),
    (r"[a-zA-Z_]+([ ]+([a-zA-Z_])+)*", String.Symbol),
    # (r"[a-zA-Z_]\w*", Name),
    (r"\d+", Number),
    (r"=", Operator.Assignment),
    (r"\.", Operator.Dot),
    # (r"\+", Operator.Plus),
    # (r"-", Operator.Minus),
    # (r"\*", "MULTIPLY"),
    # (r"/", "DIVIDE"),
    (r"\(", Operator.LParen),
    (r"\)", Operator.RParen),
    # (r"=", Operator.Equal),
    (r":", Operator.Colon),
    (r";", Operator.Semicolon),
    (r"\n", Generic.Newline),
    (r"^[ \t]+\b", Whitespace.Indent),  # Leading whitespace
    (r"[ \t]+", Whitespace),  # Ignore whitespace
]


@dataclass
@rich.repr.auto
class Token:
    token_type: tuple
    value: str
    pos: int
    line: int
    col: int


# lineno: int = -1  # Zero-indexed
# end_lineno: int = -1  # Zero-indexed
# col_offset: int = -1  # Zero-indexed, relative to the starting line
# end_col_offset: int = -1  # Zero indexed, relative to the ending line

EndOfFile = PygmentsToken.EndOfFile


class PygmentsSwornLexer(RegexLexer):
    """Pygments Lexer for Sworn script language."""

    name = "Sworn"
    url: str = "https://github.com/gbrandt1/pysworn"
    aliases = ["sworn"]
    filenames = ["*.sworn", "*.pysworn"]
    tokens = {"root": state}


@rich.repr.auto
class Lexer:
    """Lexer for Sworn script language."""

    def __init__(self, rules=state) -> None:
        self.rules = rules

        # Compile regex patterns with named groups
        regex_parts: list[str] = []
        self.group_type: dict[str, Any] = {}
        for idx, (regex, token_type) in enumerate(rules):
            groupname = f"GROUP{idx}"
            regex_parts.append(f"(?P<{groupname}>{regex})")
            self.group_type[groupname] = token_type
        self.regex = re.compile("|".join(regex_parts), re.MULTILINE)

        # self.tokens: list[tuple[type, str, int, int, int]] = []
        self.tokens: list[Token] = []

    def tokenize(self, text: str) -> list[Token]:
        """Tokenize a string into a list of (token_type, value, position) tuples."""
        # TODO: Add line and column tracking, indentation stack
        pos = 0
        line = 1
        col = 0

        while pos < len(text):
            match = self.regex.match(text, pos)

            if not match:
                msg = f"Unexpected character in line {line} at column {col}"
                raise ValueError(msg)
            groupname = match.lastgroup
            if not groupname:
                raise ValueError()

            token_type = self.group_type[groupname]
            value = match.group(groupname)
            if token_type == Whitespace.Newline:
                line += 1
                col = 0
            if token_type == String.Markdown:
                line += value.count("\n")
            col += len(value)
            self.tokens.append(Token(token_type, value, pos, line, col))
            pos = match.end()
            log.debug(self.tokens[-1])

        self.tokens.append(Token(EndOfFile, "", pos, line, 0))
        return self.tokens

    def clean_tokens(self) -> list[Token]:
        # strip comments
        tokens = [t for t in self.tokens if t.token_type not in Comment]
        # merges semicolons and newlines
        tokens_ = []
        semicolon = False
        for t in tokens:
            if not semicolon and (
                t.token_type is Operator.Semicolon or t.token_type is Generic.Newline
            ):
                t.token_type = Operator.Semicolon
                t.value = ";"
                tokens_.append(t)
                semicolon = True
            elif t.token_type is Generic.Newline or t.token_type is Whitespace:
                continue
            else:
                tokens_.append(t)
                semicolon = False
        return tokens_


def print_untokenize(tokens: list[Any]):
    untokenized = ""
    for token in tokens:
        untokenized += token.value
    # print("Untokenized:")
    # print(untokenize)

    # print(STYLE_MAP.keys())
    # print("Pygments Highlighted:")
    # print(highlight(untokenize, SwornLexer(), TerminalFormatter(style="monokai")))

    syntax = Syntax(
        untokenized,
        PygmentsSwornLexer(),
        # theme="gruvbox-dark",
        # theme="fruity",
        theme="native",
        line_numbers=True,
    )
    print(syntax)


def try_lexer():
    lexer = Lexer(state)
    text = ""
    with open("example.sworn", "r") as f:
        text = f.read()

    try:
        lexer.tokenize(text)
    except ValueError as e:
        print(f"\n{e}")
        line = lexer.tokens[-1].line - 1
        col = lexer.tokens[-1].col - 1
        print(f"[red]{text.split('\n')[line]}\n{' ' * col}^")
        return
    print_untokenize(lexer.tokens)


if __name__ == "__main__":
    from rich.logging import RichHandler

    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )

    # log.debug(lexer)

    try_lexer()
