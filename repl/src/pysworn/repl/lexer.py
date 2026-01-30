import re

import rich.repr
from pygments import highlight
from pygments.formatters import TerminalTrueColorFormatter as TerminalFormatter
from pygments.lexer import RegexLexer
from pygments.styles import STYLE_MAP
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    String,
    Whitespace,
)
from rich import print
from rich.syntax import Syntax

triple_quoted_string = (
    r'("""(?:[^"\\]|\\.|"(?="))*"""|\'\'\'(?:[^\'\\]|\\.|\'(?=\'\'))*\'\'\')'
)
double_quoted_string = r'"(?:\\.|[^"\\n])*"'
single_quoted_string = r"'([^'\\]*(?:\\.[^'\\]*)*)'"

keywords = [
    "play",
    "seed",
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
]
keywords_regex = r"\b(" + "|".join(keywords) + r")\b"

state = [
    (r"#.*", Comment.Hashbang),
    (triple_quoted_string, String.Multiline),
    (double_quoted_string, String.Double),
    (single_quoted_string, String.Single),
    (keywords_regex, Keyword),
    (r"[a-zA-Z_]\w*", Name),
    (r"\d+", Number.Integer),
    (r"\+", Operator.Plus),
    (r"-", Operator.Minus),
    # (r"\*", "MULTIPLY"),
    # (r"/", "DIVIDE"),
    # (r"\(", "LPAREN"),
    # (r"\)", "RPAREN"),
    (r"=", Operator.Assignment),
    (r":", Operator.Colon),
    (r"\n", Whitespace.Newline),
    (r"^\s+", Whitespace),  # Leading whitespace
    (r"\s+", Whitespace),  # Ignore whitespace
]


class SwornLexer(RegexLexer):
    name = "Sworn"
    url = "https://github.com/gbrandt1/pysworn"
    aliases = ["sworn"]
    filenames = ["*.sworn", "*.pysworn"]

    tokens = {
        "root": state,
    }


@rich.repr.auto
class Lexer:
    def __init__(self, rules):
        self.rules = rules
        # Compile regex patterns with named groups
        regex_parts = []
        self.group_type = {}
        for idx, (regex, token_type) in enumerate(rules):
            groupname = f"GROUP{idx}"
            regex_parts.append(f"(?P<{groupname}>{regex})")
            self.group_type[groupname] = token_type
        self.regex = re.compile("|".join(regex_parts), re.MULTILINE)

    def tokenize(self, text: str) -> list[tuple[str, str, int]]:
        pos = 0
        tokens = []
        while pos < len(text):
            match = self.regex.match(text, pos)
            if not match:
                msg = f"Unexpected character at position {pos}"
                raise ValueError(msg)
            groupname = match.lastgroup
            token_type = self.group_type[groupname]
            # if token_type is None:
            #     pos = match.end()
            #     continue  # Skip tokens like whitespace
            value = match.group(groupname)
            tokens.append((token_type, value, pos))
            pos = match.end()
            print(tokens[-1])
        return tokens


lexer = Lexer(state)

# print(lexer)

tokens = lexer.tokenize("""
seed 12434231 # for reproducibility
play starsmith starforged

'''# Starforged Session

Sworn DSL Example
'''

face_danger
action roll +2

roll family name

nazari = creature
  name = 'Varou'
  health = 3
  
in control
take_decisive_action
mark progress on 
nazari
""")
for token in tokens:
    print(token)

untokenize = ""
for token in tokens:
    untokenize += token[1]  # Append the token value (index 1) to the untokenized string

print("Untokenized:")
print(untokenize)

print(STYLE_MAP.keys())
print("Pygments Highlighted:")
# print(highlight(untokenize, SwornLexer(), TerminalFormatter(style="monokai")))

syntax = Syntax(
    untokenize,
    SwornLexer(),
    theme="gruvbox-dark",
    line_numbers=True,
)
print(syntax)
