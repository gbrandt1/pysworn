from pysworn.datasworn import index
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalScroll
from textual.widget import Widget
from textual.widgets import Select


class TagOptionLists(Widget):
    DEFAULT_CSS = """
    TagOptionLists {
        height: auto;        
        * {height: auto;}
        Select {
        padding: 0 1;        
        }
    }
    """
    BINDINGS = [
        Binding("right,l", "app.focus_next", "Focus next", show=False),
        Binding("left,h", "app.focus_previous", "Focus previous", show=False),
    ]

    def __init__(self, ruleset: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ruleset = ruleset

    def compose(self) -> ComposeResult:
        with HorizontalScroll():
            tags: dict = index[self.ruleset].rules.tags
            for tag, tag_rule in tags.items():
                if not hasattr(tag_rule, "value_type"):
                    continue
                if tag_rule.value_type == "enum":
                    yield Select(
                        ((v.value, v.value) for v in tag_rule.enum),
                        prompt=tag,
                        id=tag,
                        type_to_search=True,
                        tooltip=tag_rule.description.value,
                        compact=True,
                    )
