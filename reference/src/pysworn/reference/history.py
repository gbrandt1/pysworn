from functools import partial

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widget import Widget
from textual.widgets import OptionList
from textual.widgets.option_list import Option

# from .yes_no_dialog import YesNoDialog


class Entry(Option):
    def __init__(self, history_id: int, link: str) -> None:
        super().__init__(self._as_prompt(link))
        self.history_id = history_id
        self.link = link

    @staticmethod
    def _as_prompt(link: str) -> Text:
        return Text.from_markup(
            # f"{index[link].name.value.title()}\n[i dim]{link}[/]",
            f"{link}",
            overflow="ellipsis",
        )


class History(Widget):
    """History navigation pane."""

    BINDINGS = [
        Binding("delete", "delete", "Delete the history item"),
        Binding("backspace", "clear", "Clean the history"),
    ]

    # def __init__(self, *args, **kwargs) -> None:
    #     super().__init__("History", *args, **kwargs)

    def compose(self) -> ComposeResult:
        yield OptionList()

    def set_focus_within(self) -> None:
        self.query_one(OptionList).focus(scroll_visible=False)

    def update_from(self, links: list[str]) -> None:
        option_list = self.query_one(OptionList).clear_options()
        for history_id, link in reversed(list(enumerate(links))):
            option_list.add_option(Entry(history_id, link))

    class Goto(Message):
        def __init__(self, link: str) -> None:
            super().__init__()
            self.link = link

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        assert isinstance(event.option, Entry)
        self.post_message(self.Goto(event.option.link))

    class Delete(Message):
        def __init__(self, history_id: int) -> None:
            super().__init__()
            self.history_id = history_id

    def delete_history(self, history_id: int, delete_it: bool) -> None:
        if delete_it:
            self.post_message(self.Delete(history_id))

    def action_delete(self) -> None:
        """Delete the highlighted item from history."""
        history = self.query_one(OptionList)
        if (item := history.highlighted) is not None:
            assert isinstance(entry := history.get_option_at_index(item), Entry)
            self.app.push_screen(
                YesNoDialog(
                    "Delete history entry?",
                    "Are you sure you want to delete the history entry?",
                ),
                partial(self.delete_history, entry.history_id),
            )

    class Clear(Message):
        """Message that requests that the history be cleared."""

    def clear_history(self, clear_it: bool) -> None:
        if clear_it:
            self.post_message(self.Clear())

    def action_clear(self) -> None:
        """Clear out the whole history."""
        self.app.push_screen(
            YesNoDialog(
                "Clear history?",
                "Are you sure you want to clear everything out of history?",
            ),
            self.clear_history,
        )
