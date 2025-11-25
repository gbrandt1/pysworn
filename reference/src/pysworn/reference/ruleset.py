from pysworn.datasworn import rules
from rich.traceback import install
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static, Tab, Tabs

install()


RULESETS = [
    ("classic", "[u]I[/u]ronsworn"),
    ("delve", "[u]D[/u]elve"),
    ("starforged", "[u]S[/u]tarforged"),
    ("starsmith", "S[u]t[/u]arsmith"),
    ("sundered_isles", "S[u]u[/u]ndered Isles"),
]

RULE_CATEGORIES = [
    ("oracles", "[u]O[/u]racles"),
    ("moves", "[u]M[/u]oves"),
    ("assets", "[u]A[/u]ssets"),
    ("rarities", "[u]R[/u]arities"),
    ("npcs", "[u]N[/u]pcs"),
    ("atlas", "At[u]L[/u]as"),
    ("delve_sites", "[u]S[/u]ites"),
    ("site_domains", "[u]D[/u]omains"),
    ("site_themes", "T[u]h[/u]emes"),
    ("truths", "[u]T[/u]ruths"),
]


class RuleTabs(Tabs, can_focus=True):
    CSS = """
    Tooltip {
        height: 1;
        margin: 0;
        
    }    
    """
    BINDINGS = [
        Binding("up,j", "app.focus_previous", "Focus previous"),
        Binding("down,k", "app.focus_next", "Focus next"),
    ]


class RulesetTabs(RuleTabs):
    CSS = """
    RulesetTabs {
        height: 2;
        margin: 0;
    }
    """
    group = Binding.Group("Ruleset")
    BINDINGS = [
        Binding("I", "jump_to('classic')", "Jump to Ironsworn", group=group),
        Binding("D", "jump_to('delve')", "Jump to Delve", group=group),
        Binding("S", "jump_to('starforged')", "Jump to Starforged", group=group),
        Binding("T", "jump_to('starsmith')", "Jump to Starsmith", group=group),
        Binding(
            "U", "jump_to('sundered_isles')", "Jump to Sundered Isles", group=group
        ),
    ]

    def on_mount(self) -> None:
        self.tooltip = "Select Ruleset"
        for ruleset, title in RULESETS:
            self.add_tab(Tab(title, id=ruleset))

    class RulesetChanged(Message):
        def __init__(self, ruleset: str) -> None:
            super().__init__()
            self.ruleset = ruleset

    def action_jump_to(self, ruleset: str) -> None:
        self.active = ruleset

    @on(Tabs.TabActivated)
    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        event.stop()
        if event.tab.id:
            self.post_message(self.RulesetChanged(event.tab.id))


class RuleCategoryTabs(RuleTabs):
    group = Binding.Group("Category")
    BINDINGS = [
        Binding("O", "jump_to('oracles')", "Jump to Oracles", group=group),
        Binding("M", "jump_to('moves')", "Jump to Moves", group=group),
        Binding("A", "jump_to('assets')", "Jump to Assets", group=group),
        Binding("R", "jump_to('rarities')", "Jump to Rarities", group=group),
        Binding("N", "jump_to('npcs')", "Jump to NPCs", group=group),
        Binding("L", "jump_to('atlas')", "Jump to Atlas", group=group),
        Binding("S", "jump_to('delve_sites')", "Jump to Delve Sites", group=group),
        Binding("D", "jump_to('site_domains')", "Jump to Site Domains", group=group),
        Binding("H", "jump_to('site_themes')", "Jump to Site Themes", group=group),
        Binding("T", "jump_to('truths')", "Jump to Truths", group=group),
    ]

    ruleset: reactive[str] = reactive(RULESETS[0][0])

    def compose(self) -> ComposeResult:
        yield Tabs(*[Tab(title, id=category) for category, title in RULE_CATEGORIES])

    def on_mount(self) -> None:
        self.tooltip = "Select Rule Category"

    def watch_ruleset(self, value: str) -> None:
        for category, title in RULE_CATEGORIES:
            if len(getattr(rules[self.ruleset], category, {})):
                self.enable(category)
            else:
                self.disable(category)
        self.active = "oracles"

    def action_jump_to(self, category: str) -> None:
        self.active = category

    class CategoryChanged(Message):
        def __init__(self, category: str) -> None:
            super().__init__()
            self.category = category


if __name__ == "__main__":

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

    app = RulesetTabsApp()
    app.run()
