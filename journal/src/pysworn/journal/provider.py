from functools import partial

from pysworn.datasworn import index
from textual.app import App, ComposeResult
from textual.command import DiscoveryHit, Hit, Hits, Provider
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, RichLog


class PyswornCommands(Provider):
    """A command provider to provide pysworn commands based on index entries."""

    links: list[tuple[str, str]]

    def _read_links(self) -> list[tuple[str, str]]:
        links_ = []
        for link in index.keys():
            if ".row:" in link:
                continue
            if ":" not in link:
                links_.append((link, link))
                continue
            links_.append((link.split(":")[1], link))
        self.app.log(f"Read {len(links_)} links")
        return links_

    async def startup(self) -> None:
        """Called once when the command palette is opened, prior to searching."""
        worker = self.app.run_worker(self._read_links, thread=True)
        self.links = await worker.wait()

    async def search(self, query: str) -> Hits:
        """Search for commands."""
        matcher = self.matcher(query)

        app = self.app
        assert isinstance(app, ProviderApp)

        for cmd, link in self.links:
            score = matcher.match(cmd)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(cmd),
                    partial(app.view_link, link),
                    help=f"{type(index[link]).__name__} [i dim]{link}",
                )

    async def discover(self) -> Hits:
        app = self.app
        assert isinstance(app, ProviderApp)
        for cmd, link in self.links:
            yield DiscoveryHit(
                f"{cmd}",
                partial(app.view_link, link),
                help=f"{type(index[link]).__name__} [i dim]{link}",
            )


class ProviderApp(App):
    # COMMANDS = App.COMMANDS | {PyswornCommands}
    COMMANDS = {PyswornCommands}

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield RichLog(id="richlog")
        yield Footer()

    def view_link(self, link: str) -> None:
        from pysworn.datasworn._inspect import Inspect

        from renderables.src.pysworn.renderables.renderables import RENDERABLES

        richlog: RichLog = self.query_one("#richlog", RichLog)
        richlog.write(link)
        rule_type = link
        if ":" in link:
            rule_type = link.split(":")[0]
        renderable = RENDERABLES.get(rule_type)
        richlog.write(Inspect(index[link], max_depth=2))
        if renderable:
            richlog.write(renderable(index[link]))


def main() -> None:
    app = ProviderApp()
    app.run()


if __name__ == "__main__":
    main()
