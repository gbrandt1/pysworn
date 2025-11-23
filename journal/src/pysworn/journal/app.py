from datetime import datetime

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Input, OptionList, RichLog


class JournalApp(App):
    BINDINGS = [
        Binding("c", "clear", "Clear Journal"),
    ]

    CSS = """
    RichLog {
        height: 1fr;
        border: tall $primary;
        padding: 1 1;
    }
    Input {
        dock: bottom;
        height: 3;
        border: round $background;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            yield RichLog(id="richlog")
            yield OptionList(id="options")
        yield Input(
            placeholder="Type a message and press Enter to RichLog...",
            id="message_input",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#message_input").focus()

    def action_clear(self) -> None:
        self.query_one("#richRichLog", RichLog).clear()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self._append("INFO", text, "green")
        event.input.value = ""
        event.prevent_default()

    def _append(self, level: str, message: str, color: str) -> None:
        ts = self._timestamp()
        formatted = f"[bold {color}]{level}[/] {ts} {message}"
        richlog: RichLog = self.query_one("#richlog", RichLog)
        richlog.write(Text.from_markup(formatted))

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def main() -> None:
    JournalApp().run()


if __name__ == "__main__":
    main()
