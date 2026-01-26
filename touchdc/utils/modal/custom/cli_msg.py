"""CLI custom message dialogs"""
__all__ = ['button_option', 'option']

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod

from touchdc.ui.utils.dpi import scale
from .common import OptionMixin

class BaseCLIDialog(OptionMixin, ABC):
    def __init__(self, title="", message="", options=None, default=None, parent=None):
        self.title = title
        self.message = message
        self.options = options or []

        if default is None and self.options:
            default = self.default_fallback()
        self.default = default

    @abstractmethod
    def default_fallback(self):
        pass

    @abstractmethod
    def run(self):
        pass
        

class OptionDialog(BaseCLIDialog):
    def default_fallback(self):
        return self.options[0][1]

    def run(self):
        default_index0 = next(
            (i for i, op in enumerate(self.options) if op[1] == self.default),
            None,
        )

        print(
            "[QUESTION]"
            + (f" {self.title}:" if self.title else "")
            + (f" {self.message}" if self.message else "")
        )

        for i, op in enumerate(self.options, start=1):
            label, code, detail = self.normalize_option(op)
            prefix = f"{i}) "
            print(prefix + label)
            if detail:
                print(" " * len(prefix) + detail)

        while True:
            res = input(
                "Enter number ["
                + "/".join(str(i) for i in range(1, len(self.options) + 1))
                + "] or [c]ancel"
                + (
                    f" (Default: {default_index0 + 1})"
                    if default_index0 is not None
                    else ""
                )
                + "> "
            )
            print()

            if not res:
                return self.default

            if res.lower() in ("c", "cancel"):
                return False

            try:
                idx = int(res) - 1
                if 0 <= idx < len(self.options):
                    return self.options[idx][1]
            except ValueError:
                pass

            print("Please enter a valid option.\n")
            

class ButtonDialog(BaseCLIDialog):
    def default_fallback(self):
        return self.options[0][1] # Initially considered choosing the rightmost button (cancel) or others, but never mind

    def run(self):
        print(
            "[QUESTION]"
            + (f" {self.title}: " if self.title else " ")
            + (self.message or "")
        )

        choices = [label for label, _ in self.options]
        default_label = next(
            label for label, code in self.options if code == self.default
        )

        if len(choices) == 1:
            pass

        while True:
            res = input(
                (' | '.join([f"[{c[0].lower()}]{c[1:]}" for c in choices]))
                + (f" (Default: {default_label})" if len(choices) > 1 else " (default)")
                + "> "
            )
            print()

            if not res:
                return self.default

            r = res.strip().lower()
            for label, code in self.options:
                if r in (label.lower(), label[0].lower()):
                    return code

            print("Please enter a valid option.\n")
            
        
def option(title=None, message=None, options=None, default=None, parent=None, **kw):
    return OptionDialog(
        title=title,
        message=message,
        options=options,
        default=default,
        parent=parent,
    ).run()


def button_option(title=None, message=None, options=None, default=None, parent=None, **kw):
    return ButtonDialog(
        title=title,
        message=message,
        options=options,
        default=default,
        parent=parent,
    ).run()


#Tests
if __name__ == '__main__':
    OPTIONS = [
        ("Option A", "a", "This is the first option."),
        ("Option B", "b", "This is the second option."),
        ("Option C", "c"),
    ]

    BUTTON_OPTIONS = [
        ("Sign out", "sign_out"),
        ("Restart", "restart"),
        ("Later", "later"),
    ]
    
    print(option(title='Hello world', message='Choose an option:', options=OPTIONS))
    print(button_option(title='Hello world', message='Choose an option:', options=BUTTON_OPTIONS))
    