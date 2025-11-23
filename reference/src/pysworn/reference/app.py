import logging

from pysworn.datasworn import RulesPackageRuleset, rules

# from pysworn.tui.commands import DataswornProvider
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.logging import TextualHandler
from textual.screen import ModalScreen
from textual.widgets import Markdown

from .screen import ReferenceScreen
from .themes import deepspace_theme, delve_theme, ironsworn_theme, starforged_theme

logging.basicConfig(
    level=logging.NOTSET,
    handlers=[TextualHandler()],
)

logging.getLogger("markdown_it").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

WELCOME = """
PySworn Reference - (c) 2025 G. Brandt
"""


class Source(Markdown):
    def __init__(self, obj: RulesPackageRuleset, *args, **kwargs) -> None:
        self.source = ""
        if hasattr(obj, "title") and obj.title:
            self.source += f"# {obj.title}\n\n"
        if hasattr(obj, "authors") and obj.authors:
            self.source += ",".join([a.name for a in obj.authors])
            self.source += "\n\n"
        if hasattr(obj, "url") and obj.url:
            self.source += f"{obj.url.value}\n\n"
        if hasattr(obj, "license") and obj.license:
            self.source += f"{obj.license.value.value}\n\n"
        super().__init__(self.source, *args, **kwargs)


class SplashScreen(ModalScreen[None]):
    BINDINGS = [("escape", "app.pop_screen")]
    DEFAULT_CSS = """
    SplashScreen {
        align: center middle;        
    }
    Markdown {
        width: 1fr;
        height: 1fr;
    }
    #help-screen-text {
        width: auto;
        max-width: 70%;
        height: auto;
        max-height: 80%;
        background: $panel;
        align: center middle;
        padding: 2 4;

        & > Label#exit {
            margin-top: 1;
        }                
    }    
    """

    def compose(self) -> ComposeResult:
        with Container(id="help-screen-text"):
            yield Markdown(WELCOME)
            yield Source(rules)


class PyswornApp(App):
    TITLE = "PySworn Reference"
    CSS_PATH = ["reference.tcss", "markdown.tcss"]
    SCREENS = {
        "reference": ReferenceScreen,
        "help": SplashScreen,
    }
    # BINDINGS = [
    #     Binding("f1", "get_help", "Help"),
    # ]

    # def __init__(self) -> None:
    #     super().__init__()

    # def compose(self) -> ComposeResult:
    #     yield ReferenceScreen()

    def on_mount(self) -> None:
        for theme in (
            ironsworn_theme,
            delve_theme,
            starforged_theme,
            deepspace_theme,
        ):
            self.register_theme(theme)

        # self.theme = "ironsworn"
        # self.theme = "delve"
        # self.theme = "starforged"
        self.theme = "deepspace"

        self.push_screen(ReferenceScreen(), self.exit)

    # await self.push_screen_wait(ReferenceScreen())

    # def action_get_help(self) -> None:
    #     self.push_screen(SplashScreen())


app = PyswornApp()


def run() -> None:
    app.run()


if __name__ == "__main__":
    run()
