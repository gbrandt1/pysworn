from textual.app import ComposeResult
from textual.widget import Widget


class RulesViewer(Widget):
    def __init__(self, rules, **kwargs):
        super().__init__(**kwargs)
        self.rules = rules

    def compose(self) -> ComposeResult:
        msg = "# Rules\n"

        msg += "## Tags\n"
        for tag, rule in rules.tags:
            msg += f"{tag}: {rule}"
