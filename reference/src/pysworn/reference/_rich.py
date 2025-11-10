import re

from pysworn.datasworn._datasworn import MarkdownString


def plain(obj: MarkdownString | None):
    if not obj:
        return ""

    value = obj.value
    value = value.replace("datasworn:", "")
    # remove links
    markup_regex = r"(?:\[(?P<text>.*?)\])\((?P<link>.*?)\)"
    for m in re.findall(markup_regex, value):
        value = value.replace(f"[{m[0]}]({m[1]})", f"{m[1]}")

    # remove table substitutions
    value = re.sub(r"{{.*?}}", "", value)

    # remove bold
    value = re.sub(r"\_\_(.*?)\_\_", r"\1", value)

    return obj.value


def markup(obj: MarkdownString | None):
    """Convert to Textual + Rich markup"""
    if not obj:
        return ""

    value = obj.value
    value = value.replace("datasworn:", "")
    # remove links
    markup_regex = r"(?:\[(?P<text>.*?)\])\((?P<link>.*?)\)"
    for m in re.findall(markup_regex, value):
        # value = value.replace(f"[{m[0]}]({m[1]})", f"_{m[0]}_")
        value = value.replace(
            f"[{m[0]}]({m[1]})",
            f"[u][@click=screen.open_link('{m[1]}')]{m[0].upper()}[/][/u]",
        )

    # remove table substitutions
    value = re.sub(r"{{.*?}}", "", value)
    # convert to standard bold
    # value = value.replace("__", "**")
    value = re.sub(r"\_\_(.*?)\_\_", r"[bold]\1[/bold]", value)
    # for m in re.findall(markup_regex, value):
    #     value = value.replace(f"__{m[0]}__", f"[bold]{m[0]}[/bold]")
    # value = value.replace("__", "**")
    # return Markdown(value)
    return str(value)


def markdown(obj: MarkdownString | None):
    """Convert to Textual + Rich markdown"""
    if not obj:
        return ""

    value = obj.value

    # markup_regex = r"(?:\[(?P<text>.*?)\])\((?P<link>.*?)\)"
    # for m in re.findall(markup_regex, value):
    #     value = value.replace(
    #         f"[{m[0]}]({m[1]})",
    #         f"[{m[0]}]({m[1].removeprefix('datasworn:')})",
    #     )

    value = value.replace("datasworn:", "")

    # link outcomes
    value = value.replace("__strong hit__", "[strong hit](strong_hit)")
    value = value.replace("__weak hit__", "[weak hit](weak_hit)")
    value = value.replace("__miss__", "[miss](miss)")
    # value = value.replace("__strong hit__", "[green][strong hit](strong_hit)[/]")
    # value = value.replace("__weak hit__", "[yellow][weak hit](weak_hit)[/]")
    # value = value.replace("__miss__", "[red][miss](miss)[/]")

    # link tables
    value = re.sub(r"{{.*?}}", "", value)
    return str(value)
