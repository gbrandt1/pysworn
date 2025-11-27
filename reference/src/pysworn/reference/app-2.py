from collections import namedtuple

from pysworn.datasworn import index, rules
from pysworn.reference.tabs import (
    CategoryTabbedContent,
    CategoryViewer,
    RulesetTabbedContent,
)
from pysworn.reference.tree import ReferenceTree
from pysworn.renderables import RENDERABLES
from rich.pretty import Pretty
from rich.traceback import install
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.events import Click
from textual.reactive import reactive
from textual.widgets import Static

install()


RulesetTuple = namedtuple("RulesetTuple", "name title")


class RulesetTabsApp(App[None]):
    BINDINGS = [
        Binding("t", "toggle_tree", "Toggle Tree"),
    ]

    display_trees = reactive(True)

    def compose(self) -> ComposeResult:
        from textual.widgets import Footer, Header

        yield Header()
        yield Static()
        yield RulesetTabbedContent()
        yield Footer()

    def _update_viewer(self, id_):
        ruleset_pane = self.query_one(RulesetTabbedContent).active_pane
        ruleset = None
        category = None
        if ruleset_pane:
            ruleset = ruleset_pane.id
            category = ruleset_pane.query_one(CategoryTabbedContent).active_pane
            if category:
                category_id = category.id

        self.query_one(Static).update(
            Pretty(f"Selected: {ruleset} {category_id} {id_}")
        )
        if not category:
            return

        if ":" in id_:
            static = category.query_one(Static)
            obj = index[id_]
            rule_type = id_.split(":")[0]
            renderable = RENDERABLES.get(rule_type)
            if not renderable:
                static.update(Pretty(obj, max_depth=2, expand_all=True))
                return
            static.update(renderable(obj))
        elif "." in id_:
            # category = getattr(rules[ruleset], category_id)
            viewer = category.query_one(CategoryViewer)
            viewer.update()
        else:
            obj = index[id_]
            static = category.query_one(Static)
            static.update(Pretty(obj, max_depth=2, expand_all=True))

    def action_toggle_tree(self):
        self.display_trees = not self.display_trees
        trees = self.query("ReferenceTree")
        for tree in trees:
            tree.display = self.display_trees
        # show either navigation tree or category viewer
        categories = self.query("CategoryViewer")
        for category in categories:
            category.display = not self.display_trees

    @on(RulesetTabbedContent.RulesetChanged)
    def on_ruleset_changed(self, event: RulesetTabbedContent.RulesetChanged) -> None:
        event.stop()
        self._update_viewer(event.ruleset)

    @on(CategoryTabbedContent.CategoryChanged)
    def on_category_changed(self, event: CategoryTabbedContent.CategoryChanged) -> None:
        event.stop()
        self._update_viewer(event.category)

    def on_click(self, event: Click) -> None:
        event.stop()
        # if getattr(event, "link", None):
        self.log(f"Link: {event.style.link}")
        # self._update_viewer(event.widget.id)

    @on(ReferenceTree.ReferenceHighlighted)
    def on_node_selected(self, event: ReferenceTree.ReferenceHighlighted) -> None:
        event.stop()
        self._update_viewer(event.id_)

    def on_tab_pane_focused(self, event) -> None:
        # event.stop()
        self.log(f"Focus TabPane {event}")
        # category = ContentTab.sans_prefix(self.active)
        # self.post_message(self.CategoryChanged(f"{self.ruleset}.{category}"))


def main() -> None:
    app = RulesetTabsApp()
    app.run()


if __name__ == "__main__":
    main()
