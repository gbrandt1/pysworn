import logging
from os import pread
from sys import prefix

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler()],
)
log = logging.getLogger("pysworn.reference")
log.setLevel(logging.INFO)

logging.getLogger("markdown_it").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


def tree() -> tuple[str, logging.Logger, list]:
    """Return a tree of tuples representing the logger layout.

    Copied from https://github.com/brandon-rhodes/logging_tree/blob/master/logging_tree/nodes.py

    Each tuple looks like ``('logger-name', <Logger>, [...])`` where the
    third element is a list of zero or more child tuples that share the
    same layout.

    """
    root = ("", logging.root, [])
    nodes = {}
    items = list(logging.root.manager.loggerDict.items())
    items.sort()
    for name, logger in items:
        nodes[name] = node = (name, logger, [])
        i = name.rfind(".", 0, len(name) - 1)
        if i == -1:
            parent = root
        else:
            parent = nodes[name[:i]]
        parent[2].append(node)
    return root


def print_tree():
    from rich import print
    from rich.text import Text
    from rich.tree import Tree

    log_colors = {
        "CRITICAL": "purple",
        "FATAL": "red",
        "ERROR": "",
        "WARNING": "yellow",
        "WARN": "yellow",
        "INFO": "white",
        "DEBUG": "green",
        "NOTSET": "blue",
    }

    t = Tree("Logging", highlight=True)
    t.guide_style = "blue"

    def _add_node(tree_node, log_node):
        name, logger, children = log_node
        if isinstance(logger, logging.PlaceHolder):
            child_node = tree_node.add(f"<{logger.__class__.__name__}> '{name}'")
        else:
            level = logging.getLevelName(logger.getEffectiveLevel())
            child_node = tree_node.add(
                f"[{log_colors[level]}]{level}[/] "
                f"<{logger.__class__.__name__}> '{name}' "
            )

        for f in getattr(logger, "filters", ()):
            child_node.add(f"[bright_blue]Filter:[/] {f}")

        for h in getattr(logger, "handlers", ()):
            child_node.add(f"[bright_blue]Handle:[/] {h}")

        for child in children:
            _add_node(child_node, child)

    _add_node(t, tree())

    print(t)


# def _describe(node, parent=None):
#     name, logger, children = node
#     is_placeholder = isinstance(logger, logging.PlaceHolder)
#     if is_placeholder:
#         yield f"<--{name}"
#     else:
#         parent_is_correct = (parent is None) or (logger.parent is parent)
#         if not logger.propagate:
#             arrow = "   "
#         elif parent_is_correct:
#             arrow = "<--"
#         else:
#             arrow = " !-"
#         yield f"{arrow}{name}"

#         if not parent_is_correct:
#             if logger.parent is None:
#                 yield "   [red]Broken .parent is None, message stop here[/red]"
#             else:
#                 yield f"   [red]Broken .parent redirects to {logger.parent.name} instead[/red]"

#         if logger.level == logging.NOTSET:
#             yield f"   Level NOTSET so inherits level {logging.getLevelName(logger.getEffectiveLevel())}"
#         else:
#             yield f"   Level {logging.getLevelName(logger.level)}"

#         if not logger.propagate:
#             yield "   Propagate OFF"
#         if logger.disabled:
#             yield "   Disabled"

#         for f in logger.filters:
#             yield f"   Filter {f}"

#         for h in logger.handlers:
#             yield f"   Handler {h}"

#     if children:
#         if not is_placeholder:
#             parent = logger
#         last_child = children[-1]
#         for child in children:
#             g = _describe(child, node)
#             yield "  │\n  └\n"
#             if child is last_child:
#                 yield "   "
#             else:
#                 yield "  │"
#             for line in g:
#                 yield prefix + line
