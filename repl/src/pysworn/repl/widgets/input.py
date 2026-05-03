from dataclasses import dataclass

from pysworn.repl.widgets.history import History
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import var
from textual.suggester import SuggestFromList
from textual.widget import Widget
from textual.widgets import Input, Label
from textual.widgets.input import Selection

# COMMANDS: Final[tuple[type[InputCommand], ...]] = ()


class CommandLine(Input):
    """A command line for getting input from the user."""

    BINDINGS = [
        ("escape", "request_exit"),
        Binding(
            "up",
            "history_previous",
            tooltip="Navigate backwards through the command history",
        ),
        Binding(
            "down",
            "history_next",
            tooltip="Navigate forward through the command history",
        ),
    ]

    history: var[History] = var(History)
    """The command line history."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def _history_suggester(self) -> SuggestFromList:
        return SuggestFromList(
            [
                *reversed(list(self.history)),
            ]
        )

    def compose(self) -> ComposeResult:
        """Compose the content of the widget."""
        with Horizontal():
            yield Label("> ")
            yield Input(
                placeholder="Enter a directory, file, path or command",
                suggester=self._history_suggester,
            )

    def _watch_history(self) -> None:
        """React to history being updated."""
        if self.is_mounted:
            self.query_one(Input).suggester = self._history_suggester

    @dataclass
    class HistoryUpdated(Message):
        """Message posted when the command history is updated."""

        pass

    def handle_input(self, command: str) -> None:

        self.history.remember(command)
        self.post_message(self.HistoryUpdated())
        self.query_one(Input).value = ""
        self.query_one(Input).suggester = self._history_suggester

    @on(Input.Submitted)
    def _handle_input(self, message: Input.Submitted) -> None:
        message.stop()
        self.handle_input(message.value)

    # def action_request_exit(self) -> None:
    #     """Request that the application quits."""
    #     if self.query_one(Input).value:
    #         self.query_one(Input).value = ""
    #         self.history.last()
    #     else:
    #         self.post_message(Quit())

    def action_history_previous(self) -> None:
        """Move backwards through the command line history."""
        if value := self.history.current():
            self.query_one(Input).value = value
            self.query_one(Input).selection = Selection(0, len(value))
            self.history.backward()

    def action_history_next(self) -> None:
        """Move forwards through the command line history."""
        if self.history.forward() and (value := self.history.current_item) is not None:
            self.query_one(Input).value = value
            self.query_one(Input).selection = Selection(0, len(value))
        else:
            self.query_one(Input).value = ""


### widget.py ends here
