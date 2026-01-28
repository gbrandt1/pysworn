import fnmatch
from string import Template

from pysworn.common import datasworn_tree
from pysworn.renderables import get_renderable
from pysworn.repl.widgets.autocomplete import DataswornAutoComplete
from rich.console import Group
from rich.pretty import Pretty
from rich.theme import Theme
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.content import Content
from textual.reactive import reactive
from textual.widgets import Input, RichLog
from textual_autocomplete import (
    # AutoComplete,
    DropdownItem,
)

# for k in datasworn_tree:
# datasworn_tree[k]

datasworn_tree["classic"]
datasworn_tree["delve"]

index = datasworn_tree.index


def get_page_index_candidates():
    candidates: list[DropdownItem] = []
    page_index = {}
    for k, v in index.items():
        title = None
        page = None
        if source := getattr(v, "source", None):
            title = source.title
            page = source.page

        if title is None or page is None:
            continue

        d = page_index.setdefault(title, {})
        dd = d.setdefault(page, {})
        dd[k] = v

    for title in sorted(page_index.keys()):
        for page in sorted(page_index[title].keys()):
            for k, v in page_index[title][page].items():
                candidates.append(
                    DropdownItem(
                        k,
                        prefix=Content.from_markup(
                            f"[$text-primary on $primary-muted]{title} {page:4}: "
                        ),
                    )
                )
    return candidates


class AutoCompleteRepl(App[None]):
    CSS = """
    #inputs {
        dock: top;
        height: auto;
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

    def __init__(self) -> None:
        super().__init__()

        # self.index: dict[str, Any] = {}

        # self.candidates = list(index.keys())
        # self.candidates = get_page_index_candidates()
        self.search_terms = ["classic", "delve"]
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
        self.current: Template | None = None

    def compose(self) -> ComposeResult:
        with Container(id="top-container"):
            # with Horizontal(id="inputs"):
            #     yield Label("WHERE: ")
            #     filter_input = Input(id="filter_input")
            #     yield filter_input
            #     yield AutoComplete(target=filter_input, candidates=self.search_terms)
            repl_input = Input()
            yield repl_input
            yield DataswornAutoComplete(target=repl_input)
            # yield AutoComplete(target=repl_input, candidates=self.candidates)
            with VerticalScroll(can_focus=False):
                # preview = Static(repl_input.value, id="preview")
                # preview.can_focus = False
                # yield preview
                yield RichLog(id="richlog")

    # async def on_input_submitted(self, event: Input.Submitted) -> None:
    @on(DataswornAutoComplete.Applied)
    async def on_applied(self, event: DataswornAutoComplete.Applied):
        target = event.value
        if self.current == target:
            return
        self.current = target
        self.log(f"Target: {target}")
        self.update_object(target)

    @work()
    async def update_object(self, target: Template) -> None:
        richlog = self.query_one("#richlog", RichLog)

        ac = self.query_one(DataswornAutoComplete)
        for c in ac.chain:
            id_ = target.substitute(ruleset=c)
            if id_ in index:
                richlog.write(f"[dim green]{id_}")
                obj = index[id_]
                richlog.write(
                    Group(
                        # f"{type(obj).__name__}",
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
    for k in datasworn_tree:
        datasworn_tree[k]

    app = AutoCompleteRepl()
    app.run()
