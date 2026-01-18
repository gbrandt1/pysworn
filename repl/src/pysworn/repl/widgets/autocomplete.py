import fnmatch
from typing import Any

from datasworn.core import datasworn_tree
from textual.content import Content
from textual.widgets import Input
from textual_autocomplete import AutoComplete
from textual_autocomplete._autocomplete import DropdownItem, TargetState

RULESETS = list(datasworn_tree.keys())

datasworn_tree["classic"]


class DataswornAutoComplete(AutoComplete):
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
        self.current: str = ""
        self.root: dict[str, Any] = {k: {} for k in datasworn_tree}

        for _id in datasworn_tree.index:
            if ":" not in _id or "." in _id.split(":")[1]:
                continue
            *nodes, last = (_id.split(":")[1]).split("/")
            d = self.root
            for k in nodes:
                d = d.setdefault(k, {})
            d[last] = {}

        self.log(self.root)

    def get_candidates(self, target_state: TargetState) -> list[DropdownItem]:
        current_input = target_state.text[: target_state.cursor_position]

        results: list[DropdownItem] = []

        if " " not in current_input:
            return [DropdownItem(k, "ruleset") for k in self.root]

        tokens = current_input.split(" ")

        d = self.root
        for token in tokens:
            if token in d:
                d = d[token]

        items: list[DropdownItem] = []
        for k in d:
            target = "*".join(tokens[:-1] + [k])
            keys = list(datasworn_tree.index)
            filtered = fnmatch.filter(keys, f"*{target}")
            if not filtered:
                continue
            prefix = filtered[0].split(":")[0]
            items.append(
                DropdownItem(
                    Content.styled(k, style="$text-primary"),
                    Content.styled(f"{prefix.title()} ", style="$text-secondary"),
                )
            )

        return items

    def get_search_string(self, target_state: TargetState) -> str:
        current_input = target_state.text[: target_state.cursor_position]

        if " " in current_input:
            return current_input.split(" ")[-1]
        self.log(current_input)
        return current_input

    def apply_completion(self, value: str, state: TargetState) -> None:
        target = self.target
        current_input = state.text
        cursor_position = state.cursor_position

        try:
            replace_start_index = current_input.rindex(" ", 0, cursor_position)
        except ValueError:
            new_value = value
            new_cursor_position = len(value)
        else:
            path_prefix = current_input[: replace_start_index + 1]
            new_value = path_prefix + value
            new_cursor_position = len(path_prefix) + len(value)

        # with self.prevent(Input.Changed):
        target.value = new_value
        target.cursor_position = new_cursor_position

        self.log(f"applied: {target.value}")
        # self.post_message(Input.Submitted(target, value=target.value))

    def post_completion(self) -> None:
        if not self.target.value.endswith(" "):
            self.action_hide()
