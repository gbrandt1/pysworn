from pysworn.datasworn import rules
from pysworn.reference.tabs import RuleCategoryTabs, RulesetTabs, Static
from pysworn.reference.tree import ReferenceTree
from rich.pretty import Pretty
from rich.traceback import install
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal

install()


class RulesetTabsApp(App[None]):
    CSS = """
    RulesetTabs {
        height: 2;
    }
    """

    def compose(self) -> ComposeResult:
        from textual.widgets import Footer, Header

        yield Header()
        yield RulesetTabs()
        yield RuleCategoryTabs()
        with Horizontal():
            yield ReferenceTree("Reference")
        yield Static()
        yield Footer()

    @on(RulesetTabs.RulesetChanged)
    def on_ruleset_changed(self, event: RulesetTabs.RulesetChanged) -> None:
        from rich.pretty import Pretty

        ruleset = event.ruleset
        if ruleset:
            self.query_one(RuleCategoryTabs).ruleset = ruleset

        static = self.query_one(Static)
        static.update(Pretty(event))

    @on(RuleCategoryTabs.CategoryChanged)
    def on_category_changed(self, event: RuleCategoryTabs.CategoryChanged) -> None:
        static = self.query_one(Static)
        static.update(Pretty(event))

        ruleset = self.query_one(RuleCategoryTabs).ruleset
        tree = self.query_one(ReferenceTree)
        tree.collection = getattr(rules[ruleset], event.category)

    # @on(ReferenceTree.CollectionChanged)
    # def on_collection_changed(self, event: ReferenceTree.CollectionChanged) -> None:


def main() -> None:
    app = RulesetTabsApp()
    app.run()


if __name__ == "__main__":
    main()
