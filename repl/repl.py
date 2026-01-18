import fnmatch

from datasworn.core import datasworn_tree
from pysworn.renderables import RENDERABLE_TYPES
from pysworn.repl.widgets.autocomplete import DataswornAutoComplete
from rich.console import Group, RenderableType
from rich.panel import Panel
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Input, RichLog, Static


class AutoCompleteRepl(App[None]):
    CSS = """
    RichLog {
       height: 1fr 
    }
    Static #preview {
        dock: top;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield RichLog()
            repl_input = Input()
            with VerticalScroll(can_focus=False):
                preview = Static(repl_input.value, id="preview")
                preview.can_focus = False
                yield preview
            yield repl_input
            yield DataswornAutoComplete(target=repl_input)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        target = event.value.strip().replace(" ", "*")
        keys = list(datasworn_tree.index)
        filtered = fnmatch.filter(keys, f"*{target}")
        self.query_one(Static).update(f"{target} --> {filtered}")

        # if len(filtered) == 1:
        id_ = filtered[0]
        self.id_ = id_
        self.update_object()

    @work(exclusive=True)
    async def update_object(self) -> None:
        self.query_one(Static).update(self.get_renderable())

    def get_renderable(self) -> RenderableType:
        obj = datasworn_tree.index.get(self.id_)
        r_type = type(obj)
        if r_type in RENDERABLE_TYPES:
            renderable = RENDERABLE_TYPES.get(r_type)
        elif r_type.__mro__[1] in RENDERABLE_TYPES:
            renderable = RENDERABLE_TYPES.get(r_type.__mro__[1])
        else:
            renderable = None
        group: list[RenderableType | str] = [
            f"{self.id_} {type(obj)}",
            # f"{type(obj).__mro__}",
        ]
        if renderable:
            group.append(Panel(renderable(obj)))

        return Group(*group)

    def on_key(self, event):
        if event.key == "escape":
            event.stop()
            self.query_one(Input).focus()
        if event.key == "i":
            event.stop()
            richlog = self.query_one(RichLog)
            richlog.write(self.get_renderable())


if __name__ == "__main__":
    app = AutoCompleteRepl()
    app.run()
