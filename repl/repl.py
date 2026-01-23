import fnmatch
from collections import OrderedDict

from pysworn.common import datasworn_tree
from pysworn.renderables import get_renderable
from rich.console import Group
from rich.pretty import Pretty
from rich.theme import Theme
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Input, RichLog, Static
from textual_autocomplete import AutoComplete

# for k in datasworn_tree:
# datasworn_tree[k]

datasworn_tree["sundered_isles"]

index = datasworn_tree.human_index


class AutoCompleteRepl(App[None]):
    CSS = """
    #top-container {
        dock: top;
        height: 100%;
    }
    RichLog {
       height: 100%;
    }
    #preview {
        height: auto;
    }
    AutoComplete {
        max-height: 80%;
    }
    """

    debug: bool = reactive(False)

    def __init__(self):
        super().__init__()

        # self.index: dict[str, Any] = {}

        self.candidates = list(index.keys())

        self.console.push_theme(
            Theme(
                {
                    "markdown.item.bullet": "white",
                    "markdown.item.number": "white",
                    "markdown.hr": "white",
                    "markdown.link": "italic",
                    "markdown.link_url": "italic",
                    "markdown.block_quote": "italic",
                }
            )
        )

    def compose(self) -> ComposeResult:
        with Container(id="top-container"):
            # yield Static("", id="selected-id")
            repl_input = Input()
            yield repl_input
            # yield DataswornAutoComplete(target=repl_input)
            yield AutoComplete(target=repl_input, candidates=self.candidates)
            with VerticalScroll(can_focus=False):
                preview = Static(repl_input.value, id="preview")
                preview.can_focus = False
                yield preview
        # with VerticalScroll(can_focus=False):
        #     yield RichLog()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        # @on(DataswornAutoComplete.Applied)
        # async def on_applied(self, event: DataswornAutoComplete.Applied):
        target = event.value.strip().replace(" ", "*")
        self.log(f"Target: {target}")
        # self.app.workers.cancel_all()
        self.update_object(target)

    @work(thread=True, exclusive=True)
    async def update_object(self, target: str) -> None:
        keys = list(self.candidates)
        filtered = fnmatch.filter(keys, f"*{target}*")
        self.log(f"Filtered: {filtered[:10]}")
        # if len(filtered) == 1:
        #     self.query_one("#selected-id", Static).update(f"{target} --> {filtered}")
        # else:
        #     self.query_one("#selected-id", Static).update(
        #         f"{target} --> {len(filtered)}"
        #     )
        # return

        if not filtered:
            return
        id_ = filtered[0]
        self.id_ = id_
        obj = index[self.id_]
        self.query_one("#preview", Static).update(
            Group(
                f"{type(obj).__name__}",
                get_renderable(obj),
                Pretty(obj) if self.debug else "",
            )
        )

    def on_key(self, event):
        if event.key == "escape":
            event.stop()
            self.query_one(Input).focus()

        if event.key == "d":
            event.stop()
            self.debug = not self.debug
        # if event.key == "i":
        #     event.stop()
        #     richlog = self.query_one(RichLog)
        #     richlog.write(self.get_renderable())


if __name__ == "__main__":
    app = AutoCompleteRepl()
    app.run()
