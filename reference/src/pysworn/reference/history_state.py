from collections import deque
from typing import Final


class History:
    MAXIMUM_HISTORY_LENGTH: Final[int] = 256

    def __init__(self, history: list[str] | None = None) -> None:
        self._history: deque[str] = deque(
            history or [], maxlen=self.MAXIMUM_HISTORY_LENGTH
        )
        self._current: int = max(len(self._history) - 1, 0)

    @property
    def link(self) -> str | None:
        try:
            return self._history[self._current]
        except IndexError:
            return None

    @property
    def current(self) -> int | None:
        return None if self.link is None else self._current

    @property
    def links(self) -> list[str]:
        return list(self._history)

    def remember(self, link: str) -> None:
        self._history.append(link)
        self._current = len(self._history) - 1

    def back(self) -> bool:
        if self._current:
            self._current -= 1
            return True
        return False

    def forward(self) -> bool:
        if self._current < len(self._history) - 1:
            self._current += 1
            return True
        return False

    def __delitem__(self, index: int) -> None:
        del self._history[index]
        self._current = max(len(self._history) - 1, self._current)


history = History()
