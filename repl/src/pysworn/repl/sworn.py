import logging
import sys
from pathlib import Path
from typing import Annotated, Literal

import typer
from pysworn.repl.console import ConsoleWithInputBackspaceFixed as Console
from pysworn.repl.interpreter import Interpreter
from pysworn.repl.lexer import Lexer, print_untokenize
from pysworn.repl.parser import Parser
from rich import print
from rich.logging import RichHandler

console = Console()

logging.getLogger("markdown_it").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

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

    def run_file(self, path: Path) -> None:
        src = path.read_text()
        self.run(src)

        if self.had_error:
            sys.exit(65)

        if self.had_runtime_error:
            sys.exit(70)

    def repl(self):
        while True:
            line = console.input(">>> ")
            if line:
                self.run(line + "\n")

            # Reset these so we can stay in the REPL unhindered
            self.had_error = False
            self.had_runtime_error = False

    def run(self, src: str):
        lexer = Lexer()
        lexer.tokenize(src)

        if self.highlight:
            print_untokenize(lexer.tokens)

        tokens = lexer.clean_tokens()

        if not tokens:
            log.error("No tokens found.")
            return

        if self.show_lexer:
            print("\nCleaned Tokens:\n")
            print(tokens)
            return

        parser = Parser(tokens)
        stmts = parser.parse()

        if not stmts:
            log.error("No statements found.")
            return

        if self.show_parser:
            print("Parser Output:")
            print(stmts)
            return

        if not self.interpret:
            return

        interpreter = Interpreter()
        results = interpreter.interpret(stmts)

        from rich.columns import Columns

        print(Columns(results))

        # for result in results:
        #     print(f"{type(result)}")


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
