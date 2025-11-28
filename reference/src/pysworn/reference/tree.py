from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

from rich.text import Text
from textual.binding import Binding
from textual.events import Focus
from textual.message import Message
from textual.widgets import Tree
from textual.widgets.tree import TreeNode


def colorized_label(obj, dim: bool):
    style = ""
    if hasattr(obj, "color") and obj.color:
        style = f"{obj.color.value}"
    if dim:
        style = f"dim {style}"
    if hasattr(obj, "canonical_name") and obj.canonical_name:
        return Text(str(obj.canonical_name.value), style=style)
    elif hasattr(obj, "name") and obj.name:
        return Text(str(obj.name.value), style=style)
    elif hasattr(obj, "label") and obj.label:
        return Text(str(obj.label.value), style=style)
    # elif hasattr(obj, "summary") and obj.summary:
    #     return Text(str(obj.summary.value), style=style)
    else:
        return Text(str(obj.id.value), style=style)


class PySwornTree(Tree):
    DEFAULT_CSS = """
    PySwornTree {
       height: auto; 
       width: auto;
    }
    """
    BINDINGS = [
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("K", "cursor_up_parent", "Cursor Up Parent", show=False),
        Binding("J", "cursor_down_parent", "Cursor Down Parent", show=False),
        Binding("g", "scroll_home", "Cursor To Top", show=False),
        Binding("G", "scroll_end", "Cursor To Bottom", show=False),
        Binding("enter", "select_cursor", "Select Cursor", show=False),
        Binding("space,r", "toggle_node", "Toggle Expand", show=False),
        Binding("x", "toggle_expand_all()", "Toggle expand all", show=False),
    ]

    def on_mount(self) -> None:
        super().on_mount()
        self.show_root = False
        self.guide_depth = 2

    def action_cursor_up(self) -> None:
        if self.cursor_line == 0:
            self.screen.focus_previous()
            return
        return super().action_cursor_up()

    # copied from Posting
    def action_cursor_up_parent(self) -> None:
        """Move the cursor to the previous collapsible node."""
        start_line = max(self.cursor_line - 1, 0)
        for line in range(start_line, -1, -1):
            node = self.get_node_at_line(line)
            if node and node.allow_expand:
                self.cursor_line = line
                return

    def action_cursor_down_parent(self) -> None:
        """Move the cursor to the next collapsible node."""
        max_index = len(self._tree_lines) - 1
        start_line = min(self.cursor_line + 1, max_index)
        for line in range(start_line, max_index + 1):
            node = self.get_node_at_line(line)
            if node and node.allow_expand:
                self.cursor_line = line
                return

    def action_toggle_expand_all(self):
        self.log("Toggle expand all")
        self.root.toggle_all()

    def _on_focus(self, event: Focus) -> None:
        line = self.cursor_line
        node = self.get_node_at_line(line)
        if node:
            self.post_message(Tree.NodeHighlighted(node))

    def walk_nodes(self) -> Generator[TreeNode, None, None]:
        """Walk the nodes of the tree."""
        for node in self._tree_nodes.values():
            yield node


class ReferenceTree(PySwornTree):
    @dataclass
    class ReferenceHighlighted(Message):
        id_: str | None

    @dataclass
    class NodeSelected(Message):
        id_: str | None

    def __init__(
        self,
        label: str | Text,
        collection: dict[str, object],
        data: Any | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            label, data, name=name, id=id, classes=classes, disabled=disabled
        )

        self.collection = collection

        for obj in self.collection.values():
            # if hasattr(obj, "contents"):
            n = self.root.add(colorized_label(obj, False), data=obj.id.value)
            self._add_collection(n, obj)
            # else:
            # self.root.add_leaf(colorized_label(obj, False), data=obj.id.value)

        # self.log(self.tree)

    def _add_collection(self, node: TreeNode, collection):
        if hasattr(collection, "contents") and collection.contents:
            for obj in collection.contents.values():
                n = node.add_leaf(colorized_label(obj, True), data=obj.id.value)

        if hasattr(collection, "collections") and collection.collections:
            for obj in collection.collections.values():
                n = node.add(colorized_label(obj, False), data=obj.id.value)
                self._add_collection(n, obj)

        # if hasattr(collection, "options"):
        #     for obj in collection.options:
        #         n = node.add_leaf(colorized_label(obj, True), data=obj.id.value)

    @property
    def nodes(self) -> dict[str, TreeNode]:
        """Return a dict mapping node data (link) to TreeNode."""
        return {node.data: node for node in self.walk_nodes() if node.data}

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        self.scroll_to_line(self.cursor_line)
        self.post_message(self.ReferenceHighlighted(event.node.data))
