import fnmatch
from collections import OrderedDict
from functools import cache

from pysworn.common import datasworn_tree
from pysworn.renderables import get_renderable
from pysworn.repl.widgets.autocomplete import DataswornAutoComplete
from rich.console import Group
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Input, RichLog, Static
from textual_autocomplete import AutoComplete

for k in datasworn_tree:
    datasworn_tree[k]

datasworn_tree.index = OrderedDict(sorted(datasworn_tree.index.items(), key=len))


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
    """

    @cache
    def get_candidates(self) -> list[str]:
        candidates = []
        for k, v in datasworn_tree.index.items():
            # print(k, v.__class__)
            if ":" not in k:
                candidates.append(k)
                continue
            path = k.split(":")[1]
            if "." in path:
                continue
            candidates.append(k.split(":")[1].replace("/", " "))
        return candidates

    def compose(self) -> ComposeResult:
        with Vertical(id="top-container"):
            yield Static("", id="selected-id")
            repl_input = Input()
            yield repl_input
            # yield DataswornAutoComplete(target=repl_input)
            yield AutoComplete(target=repl_input, candidates=self.get_candidates())
            preview = Static(repl_input.value, id="preview")
            preview.can_focus = False
            yield preview
        with VerticalScroll(can_focus=False):
            yield RichLog()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        # @on(DataswornAutoComplete.Applied)
        # async def on_applied(self, event: DataswornAutoComplete.Applied):
        target = event.value.strip().replace(" ", "*")
        self.log(f"Target: {target}")
        # self.app.workers.cancel_all()
        self.update_object(target)

    @work(thread=True, exclusive=True)
    async def update_object(self, target: str) -> None:
        keys = list(datasworn_tree.index)
        filtered = fnmatch.filter(keys, f"*{target}*")
        self.log(f"Filtered: {filtered[:10]}")
        if len(filtered) == 1:
            self.query_one("#selected-id", Static).update(f"{target} --> {filtered}")
        else:
            self.query_one("#selected-id", Static).update(
                f"{target} --> {len(filtered)}"
            )
            # return

        if not filtered:
            return
        id_ = filtered[0]
        self.id_ = id_
        obj = datasworn_tree.index[self.id_]
        self.query_one("#preview", Static).update(
            Group(
                f"{type(obj).__name__}",
                get_renderable(obj),
                # Pretty(obj),
            )
        )

    def on_key(self, event):
        if event.key == "escape":
            event.stop()
            self.query_one(Input).focus()
        # if event.key == "i":
        #     event.stop()
        #     richlog = self.query_one(RichLog)
        #     richlog.write(self.get_renderable())


if __name__ == "__main__":
    app = AutoCompleteRepl()
    app.run()
