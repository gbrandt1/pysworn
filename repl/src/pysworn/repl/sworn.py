import atexit
import logging
import readline
import sys
from pathlib import Path
from typing import Annotated, Literal

import typer
from pysworn.repl.console import Completer
from pysworn.repl.interpreter import Interpreter
from pysworn.repl.lexer import Lexer, Token
from pysworn.repl.parser import Parser
from pysworn.repl.theme import pysworn_theme

# from pysworn.repl.console import ConsoleWithInputBackspaceFixed as Console
from pysworn.repl.tokens import KEYWORDS, RULESETS
from rich.columns import Columns
from rich.console import Console, RenderableType
from rich.logging import RichHandler
from rich.protocol import is_renderable

# logging.basicConfig(
#     level="WARNING",
#     format="%(message)s",
#     datefmt="[%X]",
#     handlers=[RichHandler(rich_tracebacks=True)],
# )
logging.getLogger("markdown_it").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

histfile = Path(__file__).parent / ".pysworn_history"
try:
    readline.read_history_file(histfile)
except FileNotFoundError:
    pass

readline.set_history_length(1000)
# readline.set_completer(Completer(KEYWORDS + RULESETS).complete)
readline.parse_and_bind("tab: complete")
readline.set_completer_delims(" \t\n;")
atexit.register(readline.write_history_file, histfile)

console = Console(
    theme=pysworn_theme,
    highlight=True,
    force_terminal=True,
    color_system="truecolor",
)
print = console.print


app = typer.Typer()


class Sworn:
    def __init__(
        self,
        show_lexer: bool = False,
        show_parser: bool = False,
        interpret: bool = True,
        highlight: bool = False,
    ) -> None:
        self.show_lexer = show_lexer
        self.show_parser = show_parser
        self.interpret = interpret
        self.highlight = highlight
        self.interpreter = Interpreter()
        self.had_error = False
        self.had_runtime_error = False

        self.interpreter = Interpreter()

    def run_file(self, path: Path) -> None:
        src = path.read_text()
        self.run(src)

        if self.had_error:
            sys.exit(65)

        if self.had_runtime_error:
            sys.exit(70)

    def repl(self):
        while True:
            # console.print()
            line = input("⬡⬡⬡ ")
            try:
                result = self.run(line + "\n")
                print(Columns(result, expand=True))
            except Exception as exc:
                print(exc)

            # Reset these so we can stay in the REPL unhindered
            self.had_error = False
            self.had_runtime_error = False

    def run(self, src: str):
        lexer = Lexer(src)
        tokens = lexer.scan_tokens()

        if lexer.errors or not tokens:
            self.had_error = True
            return lexer.errors

        parser = Parser(tokens, error_handler=self)
        stmts = parser.parse()

        if self.highlight:
            print(lexer.untokenize())

        if self.show_lexer:
            print(lexer)

        if self.show_parser:
            print("Parser Output:")
            print(stmts)

        if not self.interpret:
            return []

        results = self.interpreter.interpret(stmts)
        results = [r if is_renderable(r) else repr(r) for r in results]
        return results

    def error(self, token: Token, message: str | RenderableType):
        self.had_error = True
        log.error(f"[line {token.line}] {message}")


@app.command()
def main(
    script: Annotated[Path | None, typer.Argument(help="Sworn script to run.")] = None,
    scanner: Annotated[
        bool, typer.Option("--lexer", help="Print lexer output.")
    ] = False,
    parser: Annotated[
        bool, typer.Option("--parser", help="Print parser output.")
    ] = False,
    log_level: Annotated[
        Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        typer.Option("--log-level", "-l", help="Logging level.", case_sensitive=False),
    ] = "WARNING",
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            "-i",
            help="Drop into interactive mode after running script.",
        ),
    ] = False,
    exit_: Annotated[
        bool,
        typer.Option("--exit", "-x", help="Exit after running lexer and parser."),
    ] = False,
    highlight: Annotated[
        bool,
        typer.Option("--highlight", "-H", help="Print syntax highlighted script."),
    ] = False,
):
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    log.debug(f"Running with log level: {log_level}")

    sworn = Sworn(
        show_lexer=scanner,
        show_parser=parser,
        interpret=not exit_,
        highlight=highlight,
    )
    if not script:
        sworn.repl()
    else:
        sworn.run_file(script)
        if interactive:
            sworn.repl()


if __name__ == "__main__":
    app()
