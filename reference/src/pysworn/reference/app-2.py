from collections import namedtuple

from pysworn.reference.tabbed_content import (
    CategoryTabbedContent,
    RulesetTabbedContent,
)
from pysworn.reference.tree import ReferenceTree
from rich.pretty import Pretty
from rich.traceback import install
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Click
from textual.reactive import reactive
from textual.widgets import Static

install()


RulesetTuple = namedtuple("RulesetTuple", "name title")


class RulesetTabsApp(App[None]):
    DEFAULT_CSS = """
    RulesetTabbedContent {
        height: 1fr;
        width: 1fr;
    }
    """
    BINDINGS = [
        Binding("t", "toggle_tree", "Toggle Tree"),
    ]

    display_trees = reactive(True)

    def compose(self) -> ComposeResult:
        from textual.widgets import Footer, Header

        yield Header()
        yield RulesetTabbedContent()
        yield Static()
        yield Footer()

    def _update_viewer(self, id_):
        ruleset_pane = self.query_one(RulesetTabbedContent).active_pane
        ruleset = None
        category = None
        category_id = None
        if ruleset_pane:
            ruleset = ruleset_pane.id
            category = ruleset_pane.query_one(CategoryTabbedContent).active_pane
            if category:
                category_id = category.id

        self.query_one(Static).update(
            Pretty(f"Selected: {ruleset} {category_id} {id_}")
        )

    def action_toggle_tree(self):
        # show either navigation tree or category viewer
        self.display_trees = not self.display_trees
        panes = self.query("CategoryTabPane")

        for pane in panes:
            pane.display_tree = self.display_trees

    @on(RulesetTabbedContent.RulesetChanged)
    def on_ruleset_changed(self, event: RulesetTabbedContent.RulesetChanged) -> None:
        event.stop()
        self._update_viewer(event.ruleset)

    @on(CategoryTabbedContent.CategoryChanged)
    def on_category_changed(self, event: CategoryTabbedContent.CategoryChanged) -> None:
        event.stop()
        self._update_viewer(event.category)

    @on(ReferenceTree.ReferenceHighlighted)
    def on_node_selected(self, event: ReferenceTree.ReferenceHighlighted) -> None:
        event.stop()
        self._update_viewer(event.id_)

    def on_click(self, event: Click) -> None:
        event.stop()
        link = event.style.link
        if not link:
            return
        # if isinstance(link, O):
        # self.log(f"Link: {link}")
        # self.query_one(Static).update(Pretty(f"Link: {link.__class__.__mro__}"))
        # else:
        # self.log(f"Link: {link.value}")
        self.query_one(Static).update(Pretty(f"Link: {link}"))


def main() -> None:
    app = RulesetTabsApp()
    app.run()


if __name__ == "__main__":
    main()
