from string import Template
from typing import Any

from pysworn.common import datasworn_tree
from pysworn.repl.utils import get_id_dict

# from textual.cache import LRUCache
from textual.content import Content
from textual.message import Message
from textual.widgets import Input
from textual_autocomplete import AutoComplete
from textual_autocomplete._autocomplete import DropdownItem, TargetState

RULESETS = list(datasworn_tree.keys())


class DataswornAutoComplete(AutoComplete):
    class Applied(Message):
        def __init__(self, value: str) -> None:
            self.value: str = value
            super().__init__()

    def __init__(
        self,
        target: Input | str,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            target,
            None,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.current: Template | None = None

        self.chain = ["ancient_wonders", "sundered_isles", "starforged"]
        self.root: dict[str, Any] = get_id_dict(self.chain)

        self.log(self.root)

    def get_candidates(self, target_state: TargetState) -> list[DropdownItem]:
        current_input = target_state.text[: target_state.cursor_position]

        if " " not in current_input:
            return [
                DropdownItem(
                    Content.styled(
                        k,
                        style="$text-primary",
                    ),
                    # Content.styled(
                    #     f"{type(datasworn_tree[k]).__name__} ",
                    #     style="$text-secondary",
                    # ),
                )
                for k in self.root
            ]

        tokens = current_input.split(" ")

        d = self.root
        for token in tokens:
            if token in d:
                d = d[token]

                if isinstance(d, Template):
                    self.post_message(self.Applied(d))
                    return []

        items: list[DropdownItem] = []
        for k in d:
            items.append(
                DropdownItem(
                    Content.styled(k, style="$text-primary"),
                    # Content.styled(
                    #     f"{prefix.title().replace('_', ' ')} ", style="$text-secondary"
                    # ),
                )
            )

        # self._cache[cache_key] = items
        return items

    # def get_search_string(self, target_state: TargetState) -> str:
    #     current_input = target_state.text[: target_state.cursor_position]

    #     if " " in current_input:
    #         return current_input.split(" ")[-1]
    #     self.log(f"Search string: '{current_input}'")
    #     return current_input

    # def apply_completion(self, value: str, state: TargetState) -> None:
    #     target = self.target
    #     current_input = state.text
    #     cursor_position = state.cursor_position

    #     try:
    #         replace_start_index = current_input.rindex(" ", 0, cursor_position)
    #     except ValueError:
    #         new_value = value
    #         new_cursor_position = len(value)
    #     else:
    #         path_prefix = current_input[: replace_start_index + 1]
    #         new_value = path_prefix + value
    #         new_cursor_position = len(path_prefix) + len(value)

    #     # with self.prevent(Input.Changed):
    #     target.value = new_value
    #     target.cursor_position = new_cursor_position

    #     self.log(f"Applied: {target.value}")

    # def post_completion(self) -> None:
    #     if not self.target.value.endswith(" "):
    #         self.action_hide()
