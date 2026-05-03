"""
Sworn Script Pygments style
"""

from pygments.style import Style
from pygments.token import (
    Comment,
    # Generic,
    Keyword,
    # Name,
    Number,
    Operator,
    String,
    # Token,
    # Whitespace,
    Text,
)

__all__ = ["PyswornStyle"]


class PyswornStyle(Style):
    name = "pysworn"

    background_color = "#141a1c"
    highlight_color = "#dbe0e8"
    foreground_color = "#b7c3cf"

    styles = {
        Text: "#b7c3cf",
        Comment: "#737a82",  # "#b7c3cf",
        String.Doc: "#dbe0e8 italic",
        String.Double: "#FFFF80",
        String.Single: "#FFFF00",
        Keyword.Reserved: "#ca181a bold",
        Keyword: "#8d1d82",
        String.Symbol: "#36a9e1",
        Number: "#36a9e1",
        Operator: "#FFFF00",
        Operator.Assignment: "",
        Operator.Dot: "",
        Operator.LParen: "",
        Operator.RParen: "",
        Operator.Colon: "",
        Operator.Semicolon: "",
        # Generic.Newline: "",
        # Whitespace.Indent: "",
        # Whitespace: "",
    }
