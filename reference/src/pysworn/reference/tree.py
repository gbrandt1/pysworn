from rich.text import Text
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Tree
from textual.widgets.tree import TreeNode


def colorized_label(obj, leaf: bool):
    style = ""
    if hasattr(obj, "color") and obj.color:
        style = f"{obj.color.value}"
    if leaf:
        style = f"dim {style}"
    return Text(str(obj.name.value), style=style)


class PySwornTree(Tree):
    BINDINGS = [
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("K", "cursor_up_parent", "Cursor Up Parent", show=False),
        Binding("J", "cursor_down_parent", "Cursor Down Parent", show=False),
        Binding("g", "scroll_home", "Cursor To Top", show=False),
        Binding("G", "scroll_end", "Cursor To Bottom", show=False),
        Binding("enter,l,h", "select_cursor", "Select Cursor", show=False),
        Binding("space,r", "toggle_node", "Toggle Expand", show=False),
        Binding("x", "toggle_expand_all()", "Toggle expand all", show=False),
    ]

    def on_mount(self) -> None:
        super().on_mount()
        self.show_root = False
        # self.auto_expand = True
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


class ReferenceTree(PySwornTree):
    collection: reactive[dict[str, object]] = reactive({})

    def watch_collection(self):
        self.clear()
        self.nodes = {}
        self.log(f"collection {len(self.collection)}")

        for obj in self.collection.values():
            n = self.root.add(colorized_label(obj, False), data=obj.id.value)
            self._add_collection(n, obj)

        self.log(self.tree)

    def _add_collection(self, node: TreeNode, collection):
        if hasattr(collection, "contents") and collection.contents:
            for obj in collection.contents.values():
                n = node.add_leaf(colorized_label(obj, True), data=obj.id.value)

        if hasattr(collection, "collections") and collection.collections:
            for obj in collection.collections.values():
                n = node.add(colorized_label(obj, False), data=obj.id.value)
                self._add_collection(n, obj)
