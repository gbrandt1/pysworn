"""
Regex-based lexer for Sworn script language.

The lexer reuses Pygments token types and state defintion
for direct integration with Pygments.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

import rich.repr
from pygments.lexer import RegexLexer
from pygments.token import (
    Comment,
    Generic,
    Keyword,
    Number,
    Operator,
    String,
    Whitespace,
    _TokenType,  # pyright: ignore[reportPrivateUsage]
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
# pragmas = ["match", "play", "seed"]
keywords = [
    "print",
    "roll",
    "take",
    "mark",
    # "progress roll",
    # "action roll",
    "burn",
    "in control",
    "in bad spot",
    "reset",
    # "suffer",
    "from",
]
# pragmas_regex = r"\b(" + "|".join(pragmas) + r")\b"
keywords_regex = r"\b(" + "|".join(keywords) + r")\b"

state = [
    (r"--.*$", Comment),
    (triple_quoted_string, String.Doc),
    (double_quoted_string, String.Double),
    (single_quoted_string, String.Single),
    # (pragmas_regex, Keyword.Namespace),
    (keywords_regex, Keyword),
    (r"[a-zA-Z_]+([ ]+([a-zA-Z_])+)*", String.Symbol),
    # (r"[a-zA-Z_]\w*", Name),
    (r"\d+", Number),
    (r"=", Operator.Assignment),
    # (r"\.", Operator.Dot),
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
    (r"^[ \t]+\b", Whitespace.Indent),  # Leading whitespace
    (r"[ \t]+", Whitespace),  # Ignore whitespace
]


@dataclass
@rich.repr.auto
class Token:
    token_type: _TokenType
    value: str
    pos: int
    line: int
    col: int


EndOfFile = Generic.EndOfFile


class PygmentsSwornLexer(RegexLexer):
    """Pygments Lexer for Sworn script language."""

    name = "Sworn"
    url = "https://github.com/gbrandt1/pysworn"
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
        """Tokenize a string into a list Tokens."""
        # TODO: indentation stack
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
            # log.debug(self.tokens[-1])

        self.tokens.append(Token(EndOfFile, "", pos + 1, line, col + 1))
        return self.tokens

    def clean_tokens(self) -> list[Token]:
        """
        - Remove comments.
        - Insert semicolons.
        - Merge semicolons and newlines.
        """
        tokens_ = []

        line = ""
        for t in self.tokens:
            if t.token_type is Comment:
                continue

            if t.token_type is Whitespace:
                continue

            if t.token_type is Generic.Newline:
                # insert semicolon
                if len(line) > 0 and line[-1] != ";":
                    t.token_type = Operator.Semicolon
                    t.value = ";"
                    tokens_.append(t)
                line = ""
                continue

            tokens_.append(t)
            line += t.value

        return tokens_


def print_untokenize(tokens: list[Any]):
    untokenized = ""
    for token in tokens:
        untokenized += token.value

    syntax = Syntax(
        untokenized, PygmentsSwornLexer(), theme="pysworn", line_numbers=True
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

    clean_tokens = lexer.clean_tokens()
    clean_untokenized = "  ".join([t.value for t in clean_tokens]).replace(";", "\n")
    print(clean_untokenized)
    return

    # from rich import print
    # from rich.table import Table

    # clean_tokens = lexer.clean_tokens()
    # t = Table(
    #     padding=(0, 1),
    #     highlight=True,
    #     show_edge=False,
    #     show_header=False,
    # )
    # for token in clean_tokens:
    #     t.add_row(
    #         repr(token)
    #         # repr(token.token_type),
    #         # token.value,
    #         # str(token.line),
    #         # str(token.col),
    #     )
    # print(t)


if __name__ == "__main__":
    from rich.logging import RichHandler

    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )

    try_lexer()
