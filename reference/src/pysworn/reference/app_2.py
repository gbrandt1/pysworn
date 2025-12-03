from collections import namedtuple
from pathlib import PurePath
from typing import Annotated

import typer

# from pysworn.datasworn.main import rules
from pysworn.reference.tabbed_content import (
    CategoryTabbedContent,
    RulesetTabbedContent,
)
from pysworn.reference.tree import ReferenceTree
from pysworn.renderables import get_renderable
from rich.pretty import Pretty
from rich.traceback import install
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.driver import Driver
from textual.events import Click
from textual.reactive import reactive
from textual.widgets import Static


install()


RulesetTuple = namedtuple("RulesetTuple", "name title")

typer_app = typer.Typer(no_args_is_help=True, invoke_without_command=True)


class RulesetTabsApp(App[None]):
    DEFAULT_CSS = """
    RulesetTabbedContent {
        height: 1fr;
        width: 1fr;
        &:inline {
            height: 10;
        }
    }
    Screen {        
        &:inline {
            border: none;
            height: 50vh;
            Header {
                display: none;
            }
            Footer {
                display: none;
            }
        }
    }
    """
    INLINE_PADDING = 0
    BINDINGS = [
        Binding("t", "toggle_tree", "Toggle Tree"),
    ]

    display_trees = reactive(True)
    current_id: reactive[str | None] = reactive(None)
    debug: reactive[bool] = reactive(False)

    def __init__(
        self,
        driver_class: type[Driver] | None = None,
        css_path: str | PurePath | list[str | PurePath] | None = None,
        watch_css: bool = False,
        ansi_color: bool = False,
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        from rich.theme import Theme

        self.console.push_theme(
            Theme(
                {
                    "markdown.item.bullet": "white",
                    "markdown.item.number": "white",
                    "markdown.hr": "white",
                    "markdown.link": "bold white",
                    "markdown.link_url": "underline bold white",
                    "markdown.block_quote": "italic",
                }
            )
        )

    def compose(self) -> ComposeResult:
        from textual.widgets import Footer, Header

        yield Header()
        yield RulesetTabbedContent()
        yield Static()
        yield Footer()

    def _update_viewer(self, id_):
        ruleset_pane = self.query_one(RulesetTabbedContent).active_pane
        ruleset = None
        category = None
        category_id = None
        if ruleset_pane:
            ruleset = ruleset_pane.id
            category = ruleset_pane.query_one(CategoryTabbedContent).active_pane
            if category:
                category_id = category.id

        self.query_one(Static).update(
            Pretty(f"Selected: {ruleset} {category_id} {id_}")
        )

        self.current_id = id_

    @on(RulesetTabbedContent.RulesetChanged)
    def on_ruleset_changed(self, event: RulesetTabbedContent.RulesetChanged) -> None:
        event.stop()
        self._update_viewer(event.ruleset)

    @on(CategoryTabbedContent.CategoryChanged)
    def on_category_changed(self, event: CategoryTabbedContent.CategoryChanged) -> None:
        event.stop()
        self._update_viewer(event.category)

    @on(ReferenceTree.ReferenceHighlighted)
    def on_node_selected(self, event: ReferenceTree.ReferenceHighlighted) -> None:
        event.stop()
        self._update_viewer(event.id_)

    def on_click(self, event: Click) -> None:
        event.stop()
        link = event.style.link
        if not link:
            return
        # if isinstance(link, O):
        # self.log(f"Link: {link}")
        # self.query_one(Static).update(Pretty(f"Link: {link.__class__.__mro__}"))
        # else:
        # self.log(f"Link: {link.value}")
        self.query_one(Static).update(Pretty(f"Link: {link}"))

    async def action_debug(self):
        self.debug = not self.debug
        self.log(f"Debug Mode {'enabled' if self.debug else 'disabled'}")

    async def action_toggle_tree(self):
        # show either navigation tree or category viewer
        self.display_trees = not self.display_trees
        panes = self.query("CategoryTabPane")

        for pane in panes:
            pane.display_tree = self.display_trees

    async def action_quit(self) -> None:
        if not self.current_id:
            self.exit()

        try:
            from rich.panel import Panel

            r = get_renderable(self.current_id)
            self.exit(message=Panel(r))
        except KeyError:
            self.exit()


@typer_app.command()
def main(
    log_level: Annotated[
        str, typer.Option("--log-level", "-l", help="Set the logging level")
    ] = "INFO",
    inline: Annotated[
        bool,
        typer.Option(
            "--inline",
            "-i",
            help="Run the app inline in the terminal.",
        ),
    ] = False,
) -> None:
    """PySworn UI Version 2."""
    app = RulesetTabsApp()
    app.run(inline=inline)


def run() -> None:
    typer_app()


if __name__ == "__main__":
    run()
