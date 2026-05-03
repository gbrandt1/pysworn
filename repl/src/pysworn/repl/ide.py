from pysworn.common import datasworn_tree
from pysworn.repl.interpreter import Interpreter
from pysworn.repl.lexer import KEYWORDS, Lexer
from pysworn.repl.parser import Parser
from pysworn.repl.widgets.input import CommandLine
from rich.columns import Columns
from rich.pretty import Pretty
from rich.text import Text
from textual import on
from textual.app import App
from textual.containers import VerticalScroll
from textual.suggester import SuggestFromList
from textual.widgets import Footer, Header, Input, RichLog

interpreter = Interpreter()


class SwornIDE(App[None]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.history = History()
        # self.history.load()

    def compose(self):
        yield Header()
        with VerticalScroll(id="richlog-view"):
            yield RichLog(id="richlog")

        self.input = CommandLine(
            id="prompt",
            suggester=SuggestFromList(
                KEYWORDS + list(datasworn_tree.keys()),
                case_sensitive=False,
            ),
        )

        yield self.input
        yield Footer()

    def on_mount(self):
        self.query_one("#richlog-view").anchor()
        self.query_one("#richlog-view").can_focus_children = False
        self.query_one("#prompt").focus()

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted):

        richlog = self.query_one("#richlog", RichLog)
        src = event.value + "\n"
        richlog.write(Text.from_markup(f"[yellow]{src}"))
        lexer = Lexer()
        try:
            lexer.tokenize_unprocessed(src)
        except ValueError as e:
            line = lexer.tokens[-1].line - 1
            col = lexer.tokens[-1].col
            result = f"[red]{src.split('\n')[line]}\n{' ' * col}^"
            richlog.write(result)
            return

        tokens = lexer.tokenize()
        # for token in tokens:
        #     result = Pretty(
        #         f"{token.line:>3}:{token.col:>2} <{token.token_type!r} {token.value!r}>",
        #     )
        #     richlog.write(result)

        parser = Parser(tokens, error_handler=self)
        stmts = parser.parse()
        # if not stmts:
        #     return
        # for stmt in stmts:
        #     richlog.write(stmt)

        results = interpreter.interpret(stmts)
        richlog.write(Columns(results))

        # if not interpreter.had_error:
        self.input.history.append(src)
        self.query_one("#prompt", Input).value = ""

    def on_key(self, event):
        event.stop()
        if event.key == "up":
            self.query_one("#prompt", Input).value = self.history()

    def on_exit(self, event: None):
        self.input.history.save()

    def error(self, token: Token, message: str):
        richlog = self.query_one("#richlog", RichLog)
        self.had_error = True
        richlog.write(f"[line {token.line}] {message} {token}")


if __name__ == "__main__":
    app = SwornIDE()
    app.run()
