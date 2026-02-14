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
KEYWORDS = [
    "print",
    "roll",  # "progress roll", # "action roll",
    "take",
    "mark",
    "burn",
    "in control",
    "in bad spot",
    "reset",
    # "suffer",
    "tree",
    # "truths",
    # "from",
]

ID_TYPES_REGEX = [
    r"asset",
    r"asset\.ability",
    r"asset\.ability\.move",
    r"asset\.ability\.move\.condition",
    r"asset\.ability\.move\.outcome",
    r"asset\.ability\.oracle_rollable",
    r"asset_collection",
    r"atlas_collection",
    r"atlas_entry",
    r"delve_site",
    r"delve_site\.denizen",
    r"delve_site_domain",
    r"delve_site_domain\.danger",
    r"delve_site_domain\.feature",
    r"delve_site_theme",
    r"delve_site_theme\.danger",
    r"delve_site_theme\.feature",
    r"move",
    r"move\.condition",
    r"move\.oracle_rollable",
    r"move\.oracle_rollable\.row",
    r"move\.outcome",
    r"move_category",
    r"npc",
    r"npc\.variant",
    r"npc_collection",
    r"oracle_collection",
    r"oracle_rollable",
    r"oracle_rollable\.row",
    r"rarity",
    r"truth",
    r"truth\.option",
    r"truth\.option\.oracle_rollable",
    r"truth\.option\.oracle_rollable\.row",
]

# pragmas_regex = r"\b(" + "|".join(pragmas) + r")\b"
keywords_regex = r"\b(" + "|".join(KEYWORDS) + r")\b"
# id_types_regex = ( r"\$\*?(" + "|".join(ID_TYPES_REGEX) + r")*:?"
#                   r"\*?[a-z][a-z0-9_]*(\*?/[a-z][a-z0-9_\.]*)*\*?$")
id_types_regex = r"\$[a-z0-9_:/\.\*]*$"

state = [
    (r"--.*$", Comment),
    (triple_quoted_string, String.Doc),
    (double_quoted_string, String.Double),
    (single_quoted_string, String.Single),
    # (pragmas_regex, Keyword.Namespace),
    (keywords_regex, Keyword),
    (id_types_regex, String.Identifier),
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
    (r":", Operator.Colon),
    (r";", Operator.Semicolon),
    (r"\n", Generic.Newline),
    # (r"^[ \t]+\b", Whitespace.Indent),  # Leading whitespace
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

    # name = "Sworn"
    # url = "https://github.com/gbrandt1/pysworn"
    aliases = ["sworn"]
    filenames = ["*.sworn", "*.pysworn"]
    tokens = {"root": state}


@rich.repr.auto
class Lexer:
    """Lexer for Sworn script language."""

    def __init__(self, rules: list[tuple[str, _TokenType]] = state) -> None:
        self.rules = rules

        # Compile regex patterns with named groups
        regex_parts: list[str] = []
        self.group_type: dict[str, Any] = {}
        for idx, (regex, token_type) in enumerate(rules):
            groupname = f"GROUP{idx}"
            regex_parts.append(f"(?P<{groupname}>{regex})")
            self.group_type[groupname] = token_type
        self.regex = re.compile("|".join(regex_parts), re.MULTILINE)
        
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
        tokens_: list[Token] = []

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


if __name__ == "__main__":
    from rich.logging import RichHandler

    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )

    try_lexer()
