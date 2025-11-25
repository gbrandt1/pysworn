import re

from pysworn.datasworn import rules
from rich.traceback import install
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.css.query import NoMatches
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


class PySwornTabs(Tabs, can_focus=True):
    CSS = """
    Tooltip {
        height: 1;
        margin: 0;
        
    }    
    """
    BINDINGS = [
        Binding("l", "next_tab", "Next tab", show=False),
        Binding("h", "previous_tab", "Previous tab", show=False),
        Binding("up,j", "app.focus_previous", "Focus previous"),
        Binding("down,k", "app.focus_next", "Focus next"),
    ]

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "jump_to":
            tab_id = parameters[0]
            try:
                tab_to_check = self.query_one(f"#tabs-list > Tab#{tab_id}", Tab)
            except NoMatches:
                return False
            if tab_to_check.disabled:
                return None
            return True
        return True


class RulesetTabs(PySwornTabs):
    CSS = """
    RulesetTabs {
        height: 2;
        margin: 0;
    }
    """
    group = Binding.Group("Ruleset")
    BINDING_GROUP_TITLE = "Ruleset"
    BINDINGS = [
        Binding("I", "jump_to('classic')", "Jump to Ironsworn", group=group),
        Binding("D", "jump_to('delve')", "Jump to Delve", group=group),
        Binding("S", "jump_to('starforged')", "Jump to Starforged", group=group),
        Binding("T", "jump_to('starsmith')", "Jump to Starsmith", group=group),
        Binding(
            "U", "jump_to('sundered_isles')", "Jump to Sundered Isles", group=group
        ),
    ]

    class RulesetChanged(Message):
        def __init__(self, ruleset: str) -> None:
            super().__init__()
            self.ruleset = ruleset

    def on_mount(self) -> None:
        self.tooltip = "Select Ruleset"
        for ruleset, title in RULESETS:
            self.add_tab(Tab(title, id=ruleset))

    def action_jump_to(self, ruleset: str) -> None:
        self.active = ruleset

    @on(Tabs.TabActivated)
    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        event.stop()
        if event.tab.id:
            self.post_message(self.RulesetChanged(event.tab.id))


class RuleCategoryTabs(PySwornTabs):
    group = Binding.Group("Category")
    BINDING_GROUP_TITLE = "Category"
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

    category: dict = {}

    class CategoryChanged(Message):
        def __init__(self, category: str) -> None:
            super().__init__()
            self.category = category

    def compose(self) -> ComposeResult:
        yield Tabs(*[Tab(title, id=category) for category, title in RULE_CATEGORIES])

    def on_mount(self) -> None:
        self.tooltip = "Select Rule Category"

    def watch_ruleset(self, old_ruleset: str, new_ruleset: str) -> None:
        self.category[old_ruleset] = self.active
        for category, title in RULE_CATEGORIES:
            if len(getattr(rules[new_ruleset], category, {})):
                self.enable(category)
            else:
                self.disable(category)
        self.active = self.category.get(new_ruleset, "oracles")

    def action_jump_to(self, category: str) -> None:
        self.active = category

    @on(Tabs.TabActivated)
    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        event.stop()
        if event.tab.id:
            self.post_message(self.CategoryChanged(event.tab.id))
