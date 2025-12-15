from pysworn.datasworn import index
from pysworn.datasworn.main import ParsedId
from pysworn.renderables import RuleSetRenderable

# from rich.pretty import Pretty
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.lazy import Lazy
from textual.reactive import var
from textual.widgets import Static, TabbedContent, TabPane

from .category import CategoryTabs
from .widgets.tabbed_content import PySwornTabbedContent

__all__ = [
    "RulesetTabbedContent",
]


class ProgrammingError(Exception):
    pass


RULESETS = {
    "classic": ("[u]I[/u]ronsworn", "I"),
    "delve": ("[u]D[/u]elve", "D"),
    "starforged": ("[u]S[/u]tarforged", "S"),
    "starsmith": ("S[u]t[/u]arsmith", "T"),
    "sundered_isles": ("S[u]u[/u]ndered Isles", "U"),
    "fe_runners": ("[u]F[/u]E Runners", "F"),
}

ruleset_group = Binding.Group("Ruleset")


class RulesetTabbedContent(PySwornTabbedContent):
    pass


class RulesetTabs(Vertical):
    DEFAULT_CSS = """
    RulesetTabs {
       height: auto; 
    }
    """
    BINDING_GROUP_TITLE = "Ruleset"
    BINDINGS = [
        *[
            Binding(
                f"{v[1]}", f"jump_to('{k}')", f"Jump to {v[0]}", group=ruleset_group
            )
            for k, v in RULESETS.items()
        ],
        Binding("down,j", "show_categories", "Show categories", show=False),
        Binding("up,k", "hide_categories", "Hide categories", show=False),
    ]

    current_id: var[str] = var("classic")

    def compose(self) -> ComposeResult:
        with RulesetTabbedContent():
            for ruleset, v in RULESETS.items():
                title, _ = v
                with TabPane(title, id=ruleset):
                    yield Lazy(
                        Static(
                            RuleSetRenderable(index[ruleset]),
                            id="info",
                        )
                    )
                    category = CategoryTabs(ruleset, id="category")
                    # category = Static(ruleset, id=f"category")
                    category.display = False
                    yield Lazy(category)

        self.log(self.tree)

    async def watch_current_id(self, id_):
        parsed_id = ParsedId(id_)
        ruleset = parsed_id.ruleset
        self.log(f"watch_current_id: {id_}")
        #     # with self.prevent(TabbedContent.TabActivated):
        #     #     with self.prevent(TabPane.Focused):
        self.query_one(TabbedContent).active = ruleset

    def action_jump_to(self, ruleset: str) -> None:
        self.log(f"Jumping to ruleset: {ruleset}")
        self.current_id = ruleset
        self.query_one(TabbedContent).focus()

    def action_show_categories(self):
        self.log("Show categories")
        tabbed_content = self.query_one(TabbedContent)
        active_pane = tabbed_content.active_pane
        if not active_pane:
            raise ProgrammingError("No active pane")
        active_pane.query_one("#info", Static).display = False
        category = active_pane.query_one("#category", CategoryTabs)
        category.display = True
        # category.query_one(ContentTabs).focus()
        self.app.action_focus_next()

    def action_hide_categories(self):
        self.log("Hide categories")
        tabbed_content = self.query_one(TabbedContent)
        active_pane = tabbed_content.active_pane
        if not active_pane:
            raise ProgrammingError("No active pane")
        if not active_pane.query_one(Static).display:
            active_pane.query_one(Static).display = True
            active_pane.query_one("#category", CategoryTabs).display = False
            tabbed_content.focus()
