from textual.binding import Binding
from textual.css.query import NoMatches
from textual.widgets import TabbedContent, Tabs

__all__ = [
    "PySwornTabbedContent",
]


class PySwornTabbedContent(TabbedContent):
    BINDINGS = [
        Binding("l", "next_tab", "Next tab", show=False),
        Binding("h", "previous_tab", "Previous tab", show=False),
        # Binding("down,j", "app.focus_next", "Focus next", show=False),
        # Binding("up,k", "app.focus_previous", "Focus previous", show=False),
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

    def action_next_tab(self) -> None:
        tabs = self.query_one(Tabs)
        if tabs.has_focus:
            tabs.action_next_tab()

    def action_previous_tab(self) -> None:
        tabs = self.query_one(Tabs)
        if tabs.has_focus:
            tabs.action_previous_tab()
