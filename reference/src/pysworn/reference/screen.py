from pysworn.datasworn.main import RULESETS, index, rules
from pysworn.reference import (
    VIEWER_TYPES,
    # ReferenceTree,
    RuleViewer,
)
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, VerticalScroll
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Static,
    TabbedContent,
    TabPane,
)
from textual.widgets._tabs import Tabs

from ._inspect import Inspect
from .history import History
from .history_state import history
from .logging import log
from .tree import ReferenceTree
from .viewer import RulesetViewer

# RULE_TYPES = get_rule_types()
RULE_COLLECTIONS = [
    ("oracles", "[u]O[/u]racles"),
    ("moves", "[u]M[/u]oves"),
    ("assets", "[u]A[/u]ssets"),
    ("rarities", "[u]R[/u]arities"),
    ("npcs", "[u]N[/u]pcs"),
    ("atlas", "At[u]L[/u]as"),
    ("delve_sites", "Delve [u]S[/u]ites"),
    ("site_domains", "Site [u]D[/u]omains"),
    ("site_themes", "Site T[u]h[/u]emes"),
    ("truths", "[u]T[/u]ruths"),
]


class RulesTabbedContent(TabbedContent):
    BINDINGS = [
        # Binding("l", "next_tab", "Next tab", show=False),
        # Binding("h", "previous_tab", "Previous tab", show=False),
        Binding("down", "app.focus_next", "Focus next", show=False),
        Binding("up", "app.focus_previous", "Focus previous", show=False),
    ]

    def action_next_tab(self) -> None:
        tabs = self.query_one(Tabs)
        if tabs.has_focus:
            tabs.action_next_tab()

    def action_previous_tab(self) -> None:
        tabs = self.query_one(Tabs)
        if tabs.has_focus:
            tabs.action_previous_tab()


def compose_rule_viewer_tabs(category, collection) -> ComposeResult:
    with Horizontal():
        yield ReferenceTree(
            category.title(),
            collection=collection,
            id=f"{category}-tree",
        )
        # yield VerticalScroll(
        yield ScrollableContainer(
            id=f"{category}-viewer-container",
            can_focus=False,
            can_focus_children=True,
            classes="viewer-container",
        )


def compose_ruleset_tabs(ruleset: str) -> ComposeResult:
    with RulesTabbedContent(id=f"{ruleset}-rules-tabs", classes="rules-tabs"):
        for category, title in RULE_COLLECTIONS:
            if (
                hasattr(rules[ruleset], category)
                and isinstance(collection := getattr(rules[ruleset], category), dict)
                and len(collection) > 0
            ):
                with TabPane(
                    title,
                    id=category,
                    classes="reference-tabpane",
                ):
                    yield from compose_rule_viewer_tabs(category, collection)

        with TabPane("Source"):
            yield RulesetViewer(ruleset, id=f"{ruleset}-ruleset-viewer")

        with TabPane("Rules"):
            with VerticalScroll():
                yield Static(Inspect(rules[ruleset].rules))


class ReferenceScreen(ModalScreen[str]):
    BINDINGS = [
        Binding("escape", "dismiss", "Dismiss", show=True),
        Binding("d", "debug", "Debug Mode", show=True),
        Binding("ctrl+left", "backward", "<--", show=True),
        Binding("ctrl+right", "forward", "-->", show=True),
        Binding("h", "history", "Toggle History", show=True),
        Binding("t", "tree", "Toggle ToC", show=True),
        Binding("l", "link", "Toggle link bar", show=True),
        #
        Binding("O", "oracles", "Jump to Oracles", show=False),
        Binding("M", "moves", "Jump to Moves", show=False),
        Binding("A", "assets", "Jump to Assets", show=False),
        Binding("R", "rarities", "Jump to Rarities", show=False),
        Binding("N", "npcs", "Jump to NPCs", show=False),
        Binding("S", "delve_sites", "Jump to Delve Sites", show=False),
        Binding("D", "site_domains", "Jump to Site Domains", show=False),
        Binding("H", "site_themes", "Jump to Site Themes", show=False),
        Binding("L", "atlas", "Jump to Atlas", show=False),
        Binding("T", "truths", "Jump to Truths", show=False),
    ]

    def get_category_tabs(self) -> TabbedContent:
        ruleset_tabs = self.query_one("#ruleset-tabs", TabbedContent)
        if not ruleset_tabs.active_pane:
            return
        category_tabs = ruleset_tabs.active_pane.query_one(TabbedContent)
        if not category_tabs:
            return
        return category_tabs

    def action_oracles(self):
        tabs = self.get_category_tabs()
        tabs.active = "oracles"
        tabs.focus()

    def action_moves(self):
        tabs = self.get_category_tabs()
        tabs.active = "moves"
        tabs.focus()

    def action_assets(self):
        tabs = self.get_category_tabs()
        tabs.active = "assets"
        tabs.focus()

    def action_rarities(self):
        tabs = self.get_category_tabs()
        tabs.active = "rarities"
        tabs.focus()

    def action_npcs(self):
        tabs = self.get_category_tabs()
        tabs.active = "npcs"
        tabs.focus()

    def action_delve_sites(self):
        tabs = self.get_category_tabs()
        tabs.active = "delve_sites"
        tabs.focus()

    def action_site_domains(self):
        tabs = self.get_category_tabs()
        tabs.active = "site_domains"
        tabs.focus()

    def action_site_themes(self):
        tabs = self.get_category_tabs()
        tabs.active = "site_themes"
        tabs.focus()

    def action_atlas(self):
        tabs = self.get_category_tabs()
        tabs.active = "atlas"
        tabs.focus()

    def action_truths(self):
        tabs = self.get_category_tabs()
        tabs.active = "truths"
        tabs.focus()

    debug = reactive(False)

    class Visit(Message):
        def __init__(self, link: str | None = None, remember: bool = True):
            self.link = link
            self.remember = remember
            super().__init__()

    class Selected(Message):
        def __init__(self, link: str):
            self.link = link
            super().__init__()

    class HistoryUpdated(Message):
        pass

    def compose(self) -> ComposeResult:
        # print("rules loaded: " + ", ".join(rules.keys()))
        # log.info("rules loaded: " + ", ".join(rules.keys()))
        yield Header()
        with Horizontal():
            with RulesTabbedContent(id="ruleset-tabs"):
                for ruleset in RULESETS:
                    with TabPane(ruleset.title().replace("_", " "), id=ruleset):
                        yield from compose_ruleset_tabs(ruleset)
            yield History(id="history")
        yield Static(id="current-link")
        yield Footer()

    async def on_mount(self) -> None:
        log.info("Reference Screen mounted")

        self.query_one(History).display = False
        self.query_one("#current-link", Static).display = False
        self.post_message(self.Visit())

    @on(Visit)
    async def on_visit(self, event: Visit) -> None:
        """
        Open UI at the given link
        """
        event.stop()
        link: str | None = event.link
        remember: bool = event.remember

        if not link:
            remember = False
            if history.link:
                link = history.link
            else:
                link = RULESETS[0]

        self.log(f"Visiting link {link} Remember={remember}")

        if remember and link != history.link:
            history.remember(link)
            self.post_message(self.HistoryUpdated())

        self.query_one("#current-link", Static).update(f"[i]{link}")

        ruleset_tabs = self.query_one("#ruleset-tabs", TabbedContent)

        """
        Link / id format:
        
        [id_type]:[ruleset]/[category]/[item(s)];[command(s)]
        """

        # remove commands
        if ";" in link:
            link = link.split(";")[0]

        # Link is just ruleset
        if link in RULESETS:
            ruleset_tabs.active = link
            # ruleset_viewer = self.query_one(f"#{link}-ruleset-viewer", RulesetViewer)
            # ruleset_viewer.update(link)
            return

        # else link is full id
        id_type, path = link.split(":")

        # ruleset is first token after slash
        ruleset = path.split("/")[0]
        category_tabs = ruleset_tabs.query_one(f"#{ruleset}-rules-tabs", TabbedContent)
        ruleset_tabs.active = ruleset

        # category is second token after slash
        category = path.split("/")[1]
        category, viewer = VIEWER_TYPES[id_type]
        category_tabs.active = category

        parent_link = link

        category_pane = category_tabs.active_pane
        if not category_pane:
            msg = "Collection TabPane not found"
            raise ValueError(msg)

        # Change to correct rule viewer
        viewer_container = category_pane.query_one(
            f"#{category}-viewer-container",
            ScrollableContainer,
        )
        viewer_container.scroll_home()
        await viewer_container.remove_children()
        try:
            await viewer_container.mount(
                viewer(rule_id=parent_link, id=f"{category}-viewer")
            )
        except Exception as e:
            self.log(f"Error mounting viewer: {e}")
            return

        # viewer = viewer_container.query_one(f"#{category}-viewer", RuleViewer)
        # viewer.update(parent_link)

        if parent_link != link:
            # focus item
            self.log(viewer.tree)
            for widget in viewer.query():
                if not widget.can_focus:
                    continue
                self.log(widget)
                if hasattr(widget, "rule_id") and widget.rule_id == link:
                    viewer_container.scroll_to_widget(widget)
                    viewer.scroll_to_widget(widget)
                    # widget.scroll_home()
                    self.log(f"Focused widget {widget} for link {link}")
                    break

        if self.debug:
            obj = index[link]
            await viewer_container.mount(
                Static(Inspect(obj, max_depth=2), id="rule-pretty")
            )

        # Update reference tree
        try:
            tree = category_pane.query_one(f"#{category}-tree", ReferenceTree)
            tree.collection = getattr(rules[ruleset], category)
            try:
                if (node := tree.nodes[link]) != tree.cursor_node:
                    if node.is_collapsed:
                        parent = node.parent
                        while parent:
                            parent.expand()
                            parent = parent.parent
                        self.call_after_refresh(tree.move_cursor, node)
                    self.call_after_refresh(tree.scroll_to_node, node)
            except KeyError:
                self.log(f"Node {link} not found in tree '{category}'")
        except NoMatches:
            self.log(f"Tree {category} not found")

    @on(RuleViewer.Selected)
    async def on_selected(self, event: Selected) -> None:
        event.stop()
        self.log(f"Selected {event.link}")
        # self.dismiss(event.link)
        link = event.link
        if history.link != link:
            self.post_message(self.Visit(link))

    def action_open_link(self, link: str) -> None:
        self.log(f"Action Opening link {link}")
        if history.link != link:
            self.post_message(self.Visit(link))

    async def action_debug(self):
        self.debug = not self.debug
        self.log(f"Debug Mode {'enabled' if self.debug else 'disabled'}")
        self.post_message(self.Visit(history.link, remember=False))

    async def action_dismiss(self):
        self.dismiss(history.link)

    def on_tree_node_highlighted(self, event):
        event.stop()
        if event.node.data:
            self.post_message(self.Visit(event.node.data))

    def on_key(self, event):
        if event.key == "enter":
            event.stop()
            # self.log(f"Enter {event}")
            # self.dismiss(history.link)
            self.post_message(RuleViewer.Selected(history.link))

    def on_markdown_link_clicked(self, event):
        event.stop()
        # self.log(f"Link clicked: {event.href}")
        if history.link != event.href:
            self.post_message(self.Visit(event.href))

    @on(TabbedContent.TabActivated, "#ruleset-tabs")
    def on_ruleset_tab_activated(self, event: Tabs.TabActivated) -> None:
        event.stop()
        if event.tab.id:
            ruleset = event.tab.id.split("-")[-1]
            self.post_message(self.Visit(ruleset))
            # tree.collection = getattr(rules[ruleset], "oracles")

    @on(TabbedContent.TabActivated, ".rules-tabs")
    async def on_rules_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        event.stop()
        ruleset_id = event.tabbed_content.id
        if not ruleset_id:
            return
        ruleset = ruleset_id.split("-")[0]
        category = event.pane.id
        if not category:
            return
        self.log(event, ruleset, category)
        try:
            tree = event.pane.query_one(f"#{category}-tree", ReferenceTree)
            tree.collection = getattr(rules[ruleset], category)
        except NoMatches:
            pass

    @on(DataTable.RowSelected)
    async def on_row_selected(self, event):
        self.log(f"Row selected {event.row_key}")
        self.post_message(self.Selected(event.row_key.value))

    def action_tree(self) -> None:
        ruleset_tabs = self.query_one("#ruleset-tabs", TabbedContent)
        if not ruleset_tabs.active_pane:
            return
        category_tabs = ruleset_tabs.active_pane.query_one(TabbedContent)
        if not category_tabs:
            return
        category_pane = category_tabs.active_pane
        if not category_pane:
            return
        tree = category_pane.query_one(ReferenceTree)
        tree.display = not tree.display

    def action_link(self) -> None:
        link = self.query_one("#current-link", Static)
        link.display = not link.display

    # History Commands

    def action_history(self) -> None:
        h = self.query_one("#history", History)
        h.display = not h.display
        if h.display:
            h.set_focus_within()

    def action_backward(self) -> None:
        if history.back() and history.link:
            self.log(f"Backward {history.link}")
            self.post_message(self.Visit(history.link, remember=False))

    def action_forward(self) -> None:
        if history.forward() and history.link:
            self.log(f"Forward {history.link}")
            self.post_message(self.Visit(history.link, remember=False))

    def on_reference_screen_history_updated(self, event: HistoryUpdated) -> None:
        # self.log("History Updated")
        self.query_one("#history", History).update_from(history.links)
