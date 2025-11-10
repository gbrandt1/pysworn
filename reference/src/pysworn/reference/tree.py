from pysworn.datasworn import get_parent_id, index
from rich.text import Text
from textual.widgets import Tree
from textual.widgets.tree import TreeNode


def colorize(node: TreeNode):
    if node.data not in index:
        return

    obj = index[node.data]
    if hasattr(obj, "color") and obj.color:
        style = f"{obj.color.value}"
    # elif get_parent_id(node.data) in index:
    #     obj = index[get_parent_id(node.data)]
    #     if hasattr(obj, "color") and obj.color:
    #         style=f"{obj.color.value}"
    else:
        return
    if not node.allow_expand:
        node.set_label(Text(str(node.label), style="dim"))


class ReferenceTree(
    Tree[str],
    # can_focus=False,
    # can_focus_children=True,
):
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
            n = self.root.add(obj.name.value, data=obj.id.value)
            self.add_collection(n, obj)
            self.nodes[obj.id.value] = n

        # self.root.toggle_all()

    def add_collection(self, node: TreeNode, collection):
        if hasattr(collection, "contents") and collection.contents:
            for obj in collection.contents.values():
                n = node.add_leaf(f"[dim]{obj.name.value}", data=obj.id.value)
                self.nodes[obj.id.value] = n
                # colorize(n)

        if hasattr(collection, "collections") and collection.collections:
            for obj in collection.collections.values():
                n = node.add(obj.name.value, data=obj.id.value)
                self.nodes[obj.id.value] = n
                self.add_collection(n, obj)
                # colorize(n)

    def action_toggle_expand_all(self):
        self.log("Toggle expand all")
        self.root.toggle_all()
