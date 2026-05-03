# from: https://github.com/Textualize/rich/issues/2293


import logging
from getpass import getpass
from typing import TextIO

from rich.console import Console
from rich.text import TextType

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Completer:
    def __init__(self, options):
        self.options = sorted(options)
        log.debug("Completer(%s)", self.options)

    def complete(self, text, state):
        log.debug("complete(%s, %s)", repr(text), state)
        response = None
        if state == 0:
            # This is the first time for this text, so build a match list.
            if text:
                self.matches = [s for s in self.options if s and s.startswith(text)]
                log.debug("%s matches: %s", repr(text), self.matches)
            else:
                self.matches = self.options[:]
                log.debug("(empty input) matches: %s", self.matches)

        # Return the state'th item from the match list,
        # if we have that many.
        try:
            response = self.matches[state]
        except IndexError:
            response = None
        log.debug("complete(%s, %s) => %s", repr(text), state, repr(response))
        return response


class ConsoleWithInputBackspaceFixed(Console):
    def input(
        self,
        prompt: TextType = "",
        *,
        markup: bool = True,
        emoji: bool = True,
        password: bool = False,
        stream: TextIO | None = None,
    ) -> str:
        prompt_str = ""
        if prompt:
            with self.capture() as capture:
                self.print(prompt, markup=markup, emoji=emoji, end="")
            prompt_str = capture.get()
        if self.legacy_windows:
            self.file.write(prompt_str)
            prompt_str = ""
        if password:
            result = getpass(prompt_str, stream=stream)
        else:
            if stream:
                self.file.write(prompt_str)
                result = stream.readline()
            else:
                result = input(prompt_str)
        return result
