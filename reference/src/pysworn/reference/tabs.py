import re
from calendar import c
from dataclasses import dataclass
from operator import eq
from tkinter import W

from pysworn.datasworn import rules
from pysworn.reference.tree import ReferenceTree
from rich.columns import Columns

# from rich.pretty import Pretty
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.content import Content
from textual.css.query import NoMatches
from textual.events import Focus
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, TabbedContent, TabPane, Tabs, Tree
from textual.widgets._tabbed_content import ContentTab

__all__ = [
    "PySwornTabbedContent",
    "RulesetTabbedContent",
    "CategoryTabbedContent",
]


class PySwornTabbedContent(TabbedContent):
    BINDINGS = [
        Binding("l", "next_tab", "Next tab", show=False),
        Binding("h", "previous_tab", "Previous tab", show=False),
        Binding("down,j", "app.focus_next", "Focus next", show=False),
        Binding("up,k", "app.focus_previous", "Focus previous", show=False),
    ]

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        if action == "jump_to":
            tab_id = parameters[0]
            try:
                tab_to_check = self.get_tab(tab_id)
            except NoMatches:
                return False
            if tab_to_check.disabled:
                return None
            return True
        return True

    def action_jump_to(self, tab: str) -> None:
        self.active = tab

    # def _on_focus(self, event: Focus) -> None:
    #     self.log(f"PySwornTabbedContent Focus {event}")

    def action_next_tab(self) -> None:
        tabs = self.query_one(Tabs)
        if tabs.has_focus:
            tabs.action_next_tab()

    def action_previous_tab(self) -> None:
        tabs = self.query_one(Tabs)
        if tabs.has_focus:
            tabs.action_previous_tab()


class RulesetTabbedContent(PySwornTabbedContent):
    DEFAULT_CSS = """
    CategoryTabbedContent {
        padding: 0 2;
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

    RULESET_TITLES = {
        "classic": "[u]I[/u]ronsworn",
        "delve": "[u]D[/u]elve",
        "starforged": "[u]S[/u]tarforged",
        "starsmith": "S[u]t[/u]arsmith",
        "sundered_isles": "S[u]u[/u]ndered Isles",
    }

    @dataclass
    class RulesetChanged(Message):
        ruleset: str

    ruleset = reactive("classic")

    async def on_mount(self):
        for ruleset, title in RulesetTabbedContent.RULESET_TITLES.items():
            with self.prevent(TabbedContent.TabActivated):
                await self.add_pane(TabPane(title, id=ruleset))
            pane = self.get_pane(ruleset)
            categories = CategoryTabbedContent(ruleset)
            pane.mount(categories)

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        event.stop()
        if event.tab.id:
            tab_id = ContentTab.sans_prefix(event.tab.id)
            self.post_message(self.RulesetChanged(tab_id))


class CategoryViewer(Widget):
    DEFAULT_CSS = """
    CategoryViewer {
        width: 1fr;
        height: auto;
        border: round white;
    }
    """

    def __init__(self, category: dict) -> None:
        super().__init__()
        self.category = category

    def compose(self) -> ComposeResult:
        yield Static()

    def on_mount(self):
        self.update()

    def update(self):
        msg = []
        for collection in self.category.values():
            msg.append(f'[link="{collection.id.value}"]{collection.name.value}[/link]')

        self.query_one(Static).update(
            Columns(
                msg,
                equal=True,
                column_first=True,
            )
        )


class CategoryTabPane(TabPane):
    DEFAULT_CSS = """
    CategoryTabPane {
        layout: horizontal;
    }
    # Static {
    #     height: 80%;
    # }
    """


class CategoryTabbedContent(PySwornTabbedContent):
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

    RULE_CATEGORY_TITLES = {
        "oracles": "[u]O[/u]racles",
        "moves": "[u]M[/u]oves",
        "assets": "[u]A[/u]ssets",
        "rarities": "[u]R[/u]arities",
        "npcs": "[u]N[/u]pcs",
        "atlas": "At[u]l[/u]as",
        "delve_sites": "[u]S[/u]ites",
        "site_domains": "[u]D[/u]omains",
        "site_themes": "T[u]h[/u]emes",
        "truths": "[u]T[/u]ruths",
    }

    @dataclass
    class CategoryChanged(Message):
        category: str

    def __init__(self, ruleset: str):
        super().__init__()
        self.ruleset = ruleset

    async def on_mount(self):
        for category, title in CategoryTabbedContent.RULE_CATEGORY_TITLES.items():
            with self.prevent(TabbedContent.TabActivated):
                await self.add_pane(CategoryTabPane(title, id=category))
            collection = getattr(rules[self.ruleset], category, {})
            if len(collection):
                self.enable_tab(category)
                pane = self.get_pane(category)
                with self.prevent(Tree.NodeHighlighted):
                    await pane.mount(ReferenceTree(category, collection))
                await pane.mount(CategoryViewer(collection))
                pane.query_one(CategoryViewer).display = False
            else:
                self.disable_tab(category)
        self.log(self.tree)

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        event.stop()
        if event.tab.id:
            category = ContentTab.sans_prefix(event.tab.id)
            self.post_message(self.CategoryChanged(f"{self.ruleset}.{category}"))

    # @on(Focus)
    def on_tab_pane_focused(self, event) -> None:
        self.log(f"Focus {self.active} {event}")
        # return super()._on_focus(event)
        # event.stop()

        category = ContentTab.sans_prefix(self.active)
        self.post_message(self.CategoryChanged(f"{self.ruleset}.{category}"))
        # super()._on_focus(event)
