import keyword
import re

import rich.repr
from rich import print

triple_quoted_string = (
    r'("""(?:[^"\\]|\\.|"(?="))*"""|\'\'\'(?:[^\'\\]|\\.|\'(?=\'\'))*\'\'\')'
)
double_quoted_string = r'"(?:\\.|[^"\\n])*"'
single_quoted_string = r"'([^'\\]*(?:\\.[^'\\]*)*)'"

keywords = [
    "creature",
    "item",
    "location",
    "event",
    "name",
    "health",
    "strength",
]
keywords_regex = r"\b(" + "|".join(keywords) + r")\b"

rules: list[tuple[str, str]] = [
    (r"#.*", "COMMENT"),
    (triple_quoted_string, "TRIPLE_QUOTED_STRING"),
    (double_quoted_string, "DOUBLE_QUOTED_STRING"),
    (single_quoted_string, "SINGLE_QUOTED_STRING"),
    (keywords_regex, "KEYWORD"),
    (r"[a-zA-Z_]\w*", "IDENTIFIER"),
    (r"\d+", "NUMBER"),
    (r"\+", "PLUS"),
    (r"-", "MINUS"),
    (r"\*", "MULTIPLY"),
    (r"/", "DIVIDE"),
    (r"\(", "LPAREN"),
    (r"\)", "RPAREN"),
    (r"=", "EQUALS"),
    (r":", "COLON"),
    (r"\n", "NEWLINE"),
    (r"^\s+", "INDENT"),
    (r"\s+", "WHITESPACE"),  # Ignore whitespace
]


@rich.repr.auto
class Tokenizer:
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


tokenizer = Tokenizer(rules)

# print(lexer)

tokens = tokenizer.tokenize("""
  var1 =    42 + var2
'''This is a \ntriple-quoted string'''
# single line comment
var3 = "Hello, world!"
creature:
  name = 'Goblin'
  health = 30
""")
for token in tokens:
    print(token)

untokenize = ""
for token in tokens:
    untokenize += token[1]  # Append the token value (index 1) to the untokenized string

print("Untokenized:")
print(untokenize)
