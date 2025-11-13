from rich.text import Text
from textual.widgets import Tree
from textual.widgets.tree import TreeNode


def colorized_label(obj, leaf: bool):
    style = ""
    if hasattr(obj, "color") and obj.color:
        style = f"{obj.color.value}"
    if leaf:
        style = f"dim {style}"
    return Text(str(obj.name.value), style=style)


class ReferenceTree(
    Tree[str],
):
    # can_focus = False
    # can_focus_children = True
    BINDINGS = [
        ("x", "toggle_expand_all()", "Toggle expand all"),
    ]

    def __init__(
        self,
        *args,
        collection: dict,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.nodes: dict[str, TreeNode] = {}
        self.show_root = False
        self.auto_expand = True
        self.guide_depth = 2

        for obj in collection.values():
            n = self.root.add(colorized_label(obj, False), data=obj.id.value)
            self.add_collection(n, obj)
            self.nodes[obj.id.value] = n

        # self.root.toggle_all()

    def add_collection(self, node: TreeNode, collection):
        if hasattr(collection, "contents") and collection.contents:
            for obj in collection.contents.values():
                n = node.add_leaf(colorized_label(obj, True), data=obj.id.value)
                self.nodes[obj.id.value] = n

        if hasattr(collection, "collections") and collection.collections:
            for obj in collection.collections.values():
                n = node.add(colorized_label(obj, False), data=obj.id.value)
                self.nodes[obj.id.value] = n
                self.add_collection(n, obj)

    def action_toggle_expand_all(self):
        self.log("Toggle expand all")
        self.root.toggle_all()
