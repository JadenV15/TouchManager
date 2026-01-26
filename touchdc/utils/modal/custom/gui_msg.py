"""GUI custom message dialogs"""
__all__ = ['button_option', 'option']

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod

from touchdc.ui.utils.dpi import scale
from .common import OptionMixin

class BaseGUIDialog(OptionMixin, tk.Toplevel, ABC): #tinyurl.com/rm36p4wk
    def __init__(self, title="", parent=None, lock=None):
        # Parent setup
        self.parent_present = True
        if parent is None:
            if tk._default_root is None:
                self.parent_present = False
                self.parent = tk.Tk()
                self.parent.geometry("1x1+0+0")
                self.parent.overrideredirect(True)
            else:
                self.parent = tk._default_root
        else:
            self.parent = parent

        # call super AFTER parent is set
        super().__init__(self.parent)

        self.title(title)
        self.resizable(False, False)

        if self.parent_present:
            self.transient(self.parent)

        self.result = False
        
        if lock:
            self.protocol("WM_DELETE_WINDOW", lambda *_: None)
        else:
            self.bind('<Escape>', lambda *_: self.on_cancel())
            self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def run(self):
        self._draw()

        # Center dialog relative to parent
        if self.parent_present:
            self.parent.update_idletasks()
            self.update_idletasks()
            x = (
                self.parent.winfo_rootx()
                + self.parent.winfo_width() // 2
                - self.winfo_width() // 2
            )
            y = (
                self.parent.winfo_rooty()
                + self.parent.winfo_height() // 2
                - self.winfo_height() // 2
            )
            self.geometry(f"+{x}+{y}")

        # Show dialog
        self.deiconify()
        self.lift()
        self.focus_force()
        self.grab_set()
        self.wait_window()# Block until closed

        # Close root only if we created it
        if not self.parent_present:
            self.parent.destroy()

        return self.result

    def close(self):
        self.grab_release()
        self.destroy()

    @abstractmethod
    def _draw(self):
        pass
        
    @abstractmethod
    def on_cancel(self):
        pass


class OptionDialog(BaseGUIDialog):
    def __init__(self, title="", message="", options=None, default=None, parent=None, lock=True):
        self.message = message
        self.options = options or []

        if default is None and self.options:
            default = self.options[0][1]
        self.default = default
        
        if lock is None:
            lock = True

        super().__init__(title, parent, lock)
        self.bind("<Return>", lambda e: self.on_ok())

    def _draw(self):
        valid_defaults = {op[1] for op in self.options}
        self.var = tk.StringVar(
            value=self.default if self.default in valid_defaults else ''
        )

        if self.message:
            ttk.Label(
                self, text=self.message, anchor="w", justify="left"
            ).pack(padx=10, pady=(10, 5), fill="x")

        for op in self.options:
            label, code, detail = self.normalize_option(op)

            frame = ttk.Frame(self)
            frame.pack(anchor="w", padx=20, pady=5, fill="x")

            rb = ttk.Radiobutton(frame, variable=self.var, value=code)
            rb.grid(row=0, column=0, rowspan=2, sticky="n")

            def select(event, v=code):
                self.var.set(v)

            name = ttk.Label(frame, text=label)
            name.grid(row=0, column=1, sticky="w")
            name.bind("<Button-1>", select)

            if detail:
                d = ttk.Label(
                    frame,
                    text=detail,
                    style="Detail.TLabel",
                    wraplength=scale(400),
                )
                d.grid(row=1, column=1, sticky="w", pady=(0, 5))
                d.bind("<Button-1>", select)

            frame.columnconfigure(1, weight=1)

        btns = ttk.Frame(self)
        btns.pack(pady=10)

        ttk.Button(btns, text="OK", command=self.on_ok).pack(side="left", padx=5)
        ttk.Button(btns, text="Cancel", command=self.on_cancel).pack(side="left", padx=5)

    def on_ok(self): # OK or Enter
        self.result = self.var.get() or False
        self.close()
        
    def on_cancel(self): # WM_DELETE_WINDOW
        self.result = False
        self.close()


class ButtonDialog(BaseGUIDialog):
    def __init__(self, title="", message="", options=None, default=None, parent=None, lock=True):
        self.message = message
        self.options = options or []

        if default is None and self.options:
            default = self.options[0][1]
        self.default = default
        
        if lock is None:
            lock = True

        super().__init__(title, parent, lock)
        self.bind("<Return>", self.on_enter)

    def _draw(self):
        if self.message:
            ttk.Label(
                self,
                text=self.message,
                anchor="center",
                justify="center",
                wraplength=scale(400),
            ).pack(padx=20, pady=20)

        btns = ttk.Frame(self)
        btns.pack(padx=10, pady=(0, 10))

        for label, code in self.options:
            btn = ttk.Button(btns, text=label,
                             command=lambda v=code: self.on_select(v))
            btn.pack(side="left", padx=5)

            if code == self.default:
                self.default_button = btn

        if hasattr(self, "default_button"):
            self.default_button.focus_set()

    def on_select(self, value):
        self.result = value
        self.close()

    def on_enter(self, event=None): # Enter keypress
        self.result = self.default
        self.close()

    def on_cancel(self):
        self.result = False
        self.close()

def option(title=None, message=None, options=None, default=None, parent=None, lock=None, **kw):
    return OptionDialog(
        title=title,
        message=message,
        options=options,
        default=default,
        parent=parent,
        lock=lock
    ).run()

def button_option(title=None, message=None, options=None, default=None, parent=None, lock=None, **kw):
    return ButtonDialog(
        title=title,
        message=message,
        options=options,
        default=default,
        parent=parent,
        lock=lock
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
    