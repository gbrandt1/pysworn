from dataclasses import dataclass
from re import sub

from pysworn.datasworn import index, rules
from pysworn.datasworn.main import ParsedId
from pysworn.reference.tree import ReferenceTree
from pysworn.renderables import CategoryRenderable, get_renderable
from rich.columns import Columns

# from rich.pretty import Pretty
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.content import Content
from textual.css.query import NoMatches
from textual.lazy import Lazy
from textual.message import Message
from textual.reactive import reactive, var
from textual.widget import Widget
from textual.widgets import Pretty, Static, TabbedContent, TabPane
from textual.widgets._content_switcher import ContentSwitcher
from textual.widgets._tabbed_content import ContentTab

from .widgets.tabbed_content import PySwornTabbedContent

__all__ = [
    "CategoryTabPane",
    "CategoryTabbedContent",
]


def kebab(s):
    return "-".join(
        sub(
            r"(\s|[_:/]|-)+",
            " ",
            sub(
                r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
                lambda mo: " " + mo.group(0).lower(),
                s,
            ),
        ).split()
    )


class ProgrammingError(Exception):
    pass


class CategoryViewer(Widget):
    can_focus = True
    DEFAULT_CSS = """
    CategoryViewer {
        width: auto;
        height: auto;
        # border: round white;
    }
    """

    def __init__(self, category: dict, id: str) -> None:
        super().__init__(id=id)
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
    BINDINGS = [
        Binding("d", "toggle_debug", "Toggle Debug View"),
    ]
    DEFAULT_CSS = """
    CategoryTabPane {
        layout: horizontal;
    }
    Static {
        padding: 1 2;
    }
    #category-viewer {
        height: 1fr;
    }
    #tree {
        height: 1fr;
        width: auto;
    }
    #content {        
        width: 1fr;
    }
    """

    display_tree = reactive(True)
    debug = reactive(True)

    def __init__(
        self,
        ruleset: str,
        category: str,
        title: Content | str,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        self.ruleset = ruleset
        self.category = category
        self.collection = getattr(rules[self.ruleset], category, {})
        super().__init__(
            title,
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

    def compose(self) -> ComposeResult:
        if not self.collection:
            return
        with Horizontal(classes="category-pane"):
            with VerticalScroll(id=f"{self.ruleset}-{self.category}-container"):
                yield ReferenceTree(
                    self.category,
                    self.collection,
                    id=f"{self.ruleset}-{self.category}-tree",
                )
            with VerticalScroll(id=f"{self.ruleset}-{self.category}-content"):
                with ContentSwitcher(id=f"{self.ruleset}-{self.category}-switcher"):
                    yield CategoryViewer(self.collection, id=self.category)
                    yield Pretty("", id="debug")

    async def watch_display_tree(self, value):
        try:
            tree = self.query_one(ReferenceTree)
            category = self.query_one(CategoryViewer)
            tree.display = value
            category.display = not value
        except NoMatches:
            pass

    async def on_mount(self):
        self.display_tree = True

    async def on_reference_tree_reference_highlighted(self, event):
        content = self.query_one(ContentSwitcher)
        if not event.id_:
            content.current = self.category
            return
        content_id = kebab(event.id_)

        try:
            content.current = content_id
        except NoMatches:
            await content.add_content(
                Static(get_renderable(event.id_)),
                # Pretty(index[event.id_], id="{content_id}-debug", classes="debug"),
                id=content_id,
                set_current=True,
            )
            self.query_one(f"#{content_id}", Static).display = True

        self.query_one("#debug", Pretty).update(index[event.id_])

    def action_toggle_debug(self) -> None:
        self.debug = not self.debug
        self.query_one("#debug").display = self.debug


CATEGORIES = {
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


class CategoryTabbedContent(PySwornTabbedContent):
    pass


class CategoryTabs(Vertical):
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
        #
        Binding("down,j", "app.focus_next", "Focus next", show=False),
        Binding("up,k", "app.focus_previous", "Focus previous", show=False),
    ]

    current_id: var[str] = var("oracles")

    # @dataclass
    # class CategoryChanged(Message):
    #     category: str

    def __init__(self, ruleset: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ruleset = ruleset

    def compose(self) -> ComposeResult:
        with CategoryTabbedContent():
            for category, title in CATEGORIES.items():
                with TabPane(title, id=category):
                    yield Lazy(
                        Static(  # CollectionRenderable(getattr(index[self.ruleset], category)))
                            CategoryRenderable(getattr(rules[self.ruleset], category)),
                            id=category,
                        )
                    )

    def on_mount(self):
        tabbed_content = self.query_one(CategoryTabbedContent)
        for category in CATEGORIES.keys():
            if not getattr(index[self.ruleset], category):
                tabbed_content.disable_tab(category)

    # @work
    # async def add_panes(self):
    #     for category, title in RULE_CATEGORY_TITLES.items():
    #         with self.prevent(TabbedContent.TabActivated):
    #             await self.add_pane(
    #                 CategoryTabPane(self.ruleset, category, title, id=category)
    #             )
    #             try:
    #                 self.get_pane(category).query_one(ReferenceTree)
    #             except NoMatches:
    #                 self.disable_tab(category)
    #     self.loading = False

    # def on_tabbed_content_tab_activated(
    #     self, event: TabbedContent.TabActivated
    # ) -> None:
    #     event.stop()
    #     if not event.tab.id:
    #         msg = "Activated tab has no id"
    #         raise ProgrammingError(msg)
    #     category = ContentTab.sans_prefix(event.tab.id)
    #     self.log(f"Category changed to: {category}")
    #     self.post_message(self.CategoryChanged(f"{self.ruleset}.{category}"))

    # def on_tab_pane_focused(self, event) -> None:
    #     event.stop()
    #     return
    #     category = ContentTab.sans_prefix(self.active)
    #     self.post_message(self.CategoryChanged(f"{self.ruleset}.{category}"))

    # async def watch_current_id(self, id_):
    #     parsed_id = ParsedId(id_)
    #     category = parsed_id.category
    #     self.log(f"watch_current_id: {id_}")
    #     #     # with self.prevent(TabbedContent.TabActivated):
    #     #     #     with self.prevent(TabPane.Focused):
    #     self.query_one(TabbedContent).active = category

    def action_jump_to(self, category: str) -> None:
        self.log(f"Jumping to category: {category}")
        ruleset = ParsedId(self.current_id).ruleset
        self.current_id = f"{ruleset}.{category}"
        self.query_one(TabbedContent).focus()
