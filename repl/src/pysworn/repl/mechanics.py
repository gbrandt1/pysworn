from rich.console import (
    Console,
    ConsoleOptions,
    ConsoleRenderable,
    Group,
    RenderableType,
    RenderResult,
)

# class ActionRoll:
RANK: dict[str, int] = {
    "troublesome": 12,
    "dangerous": 8,
    "formidable": 4,
    "extreme": 2,
    "epic": 1,
}


class ProgessTrack:
    def __init__(
        self,
        *args,
        rank: int = RANK["formidable"],
        **kwargs,
    ):
        self.args = args
        self.kwargs = kwargs
        self.ticks = 0
        self.rank = rank

    def mark(self):
        self.ticks += rank
        self.ticks = min(self.ticks, 40)

    def __rich_console__(
        self, console: Console, options_: ConsoleOptions
    ) -> RenderResult:
        yield f"{'[✴]' * (self.ticks // 4)}[{'.' * self.ticks % 4}]"

    # ⬢ ⬡ 🟍
