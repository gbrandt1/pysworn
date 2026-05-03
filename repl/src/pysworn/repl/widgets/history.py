class History:
    def __init__(self):
        self._strings: list[str] = []
        self.history_file = ".sworn_history"
        self._current = 0

    def load(self):
        try:
            with open(self.history_file, "r") as f:
                self._strings = f.read().split("\n")
        except FileNotFoundError:
            pass

    def save(self):
        with open(self.history_file, "w") as f:
            f.write("\n".join(self._strings))

    def current(self):
        try:
            return self._strings[self._current]
        except IndexError:
            return None

    def backward(self):
        self._current = max(self._current - 1, 0)

    def forward(self):
        self._current = min(self._current + 1, len(self._strings) - 1)

    def last(self):
        self._current = len(self._strings)

    def remember(self, string: str):
        self._strings.append(string)
        self.last()
        self.save()

    def __iter__(self):
        return reversed(self._strings)
