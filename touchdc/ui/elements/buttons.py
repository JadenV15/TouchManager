"""Custom button widgets"""
__all__ = ['ButtonGroup', 'SystemButtonGroup', 'DropdownButton']

import random
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from contextlib import suppress
from matplotlib.colors import to_rgb, to_hex

from .tooltip import Tooltip
from touchdc.system.model import Device

class ButtonGroup(ttk.Frame):
    """A group of buttons functioning as a single widget, acting as both a toggle button and click buttons"""
    def __init__(
        self,
        parent,
        options,
        initial=None,
        command=None,
        font=None,
        selected_bg="#0078d7",
        selected_fg="white",
        normal_bg="#e0e0e0",
        normal_fg="black",
        border_color="#999999",
        tooltip_kwargs=None,
        btn_padx=10,
        btn_pady=5,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.parent = parent
        self.options = options
        self.command = command
        self._value = initial  # if initial else options[0][1]
        self._buttons = []
        self._state = 'normal'
        
        self.font = font or ("Segoe UI Emoji", 12)
        self._padx = btn_padx
        self._pady = btn_pady
        
        self._selected_bg = selected_bg
        self._selected_fg = selected_fg
        self._normal_bg = normal_bg
        self._normal_fg = normal_fg
        self._border_color = border_color

        tooltip_kwargs = tooltip_kwargs or {}

        # Create buttons and dividers
        for col, (label, code, desc) in enumerate(options):
            if col > 0:
                divider = tk.Frame(self, width=1, bg=self._border_color)
                divider.grid(row=0, column=col * 2 - 1, sticky="ns")

            btn = tk.Button(
                self,
                text=label,
                font=font,
                relief=tk.FLAT,
                bd=1,
                highlightthickness=0,
                bg=self._normal_bg,
                fg=self._normal_fg,
                activebackground=self._selected_bg,
                activeforeground=self._selected_fg,
                padx=self._padx,
                pady=self._pady,
                command=lambda c=code: self._on_click(c)
            )
            btn.grid(row=0, column=col * 2, sticky="nsew")
            self.columnconfigure(col * 2, weight=1)

            if desc:
                Tooltip(btn, text=desc, **tooltip_kwargs)

            self._buttons.append((btn, code))

        # Apply initial selection
        self._update_buttons()
    
    def _brightness(self, color, factor=0):
        assert 0 <= factor <= 1
        
        r, g, b = tuple(
            max(0, min(1, ch + (1 - ch) * factor))
            for ch in to_rgb(color)
        )
        
        return to_hex((r, g, b))
        
    def _convert(self, color):
        if self._state == 'disabled':
            return self._brightness(color, factor=0.25)
        else:
            return to_hex(color)
    
    def _on_click(self, code):
        if self.command:
            if self.command(self._value, code) is False:
                return

        self._value = code
        self._update_buttons()

    def _update_buttons(self):
        for btn, code in self._buttons:
            if code == self._value:
                btn.config(
                    bg=self._convert(self._selected_bg),
                    fg=self._convert(self._selected_fg)
                )
            else:
                btn.config(
                    bg=self._convert(self._normal_bg),
                    fg=self._convert(self._normal_fg)
                )

    def get(self):
        """Get the code of the currently selected button"""
        return self._value

    def set(self, value):
        """Select a button by code, without running `self.command`
        If value is None, clear the current selection
        """
        self._value = value
        self._update_buttons()
        
    def configure(self, *, state):
        """Mimicking tkinter's configure method of widgets"""
        if state == 'disable':
            state = 'disabled'
        assert state in ['disabled', 'normal', 'active']
        
        for child in self.winfo_children():
            with suppress(tk.TclError): # disabling widgets isnt that big of a deal anyway
                child.configure(state=state)
                
        self._state = state
                
    def destroy(self):
        """Destroy the widget"""
        for child in self.winfo_children():
            child.destroy()


class SystemButtonGroup(ButtonGroup):
    """Small wrapper around ButtonGroup for ease of use in the app"""
    
    # Button codes
    BTN_ENABLE  = Device.ENABLE
    BTN_DISABLE = Device.DISABLE
    BTN_NONE    = Device.NONE
    
    BTNS = (BTN_ENABLE, BTN_DISABLE, BTN_NONE)
    
    # Predefined button sets
    BTN3 = (BTN_ENABLE, BTN_DISABLE, BTN_NONE)
    BTN2 = (BTN_ENABLE, BTN_DISABLE)
    
    def __init__(self, parent, buttons: tuple = None, button_text: tuple = None, button_tips: tuple = None, **kw):
        if buttons is None:
            buttons = type(self).BTN2 # Default to BTN2
        if button_text is None:
            button_text = (name.capitalize() for name in buttons)
        if button_tips is None:
            button_tips = ('Enable the item', 'Disable the item', 'Clear the item of its value')[:len(buttons)] # Default tooltips
        
        assert all([btn in type(self).BTNS for btn in buttons])
        assert isinstance(button_text, tuple) and len(button_text) == len(buttons)
        assert isinstance(button_tips, tuple) and len(button_tips) == len(buttons)
        
        args = {
            'options': [
                (label, code, desc)
                for label, code, desc in zip(button_text, buttons, button_tips) # (label, code, desc) format
            ],
            'initial': None,
            'tooltip_kwargs': dict(wraplength=200),
            **kw
        }
            
        super().__init__(parent, **args)
        
# https://stackoverflow.com/questions/44099594/how-to-make-a-tkinter-canvas-rectangle-with-rounded-corners

class DropdownButton(ttk.Button):
    """Button that shows a dropdown menu of buttons when clicked"""
    def __init__(self, parent, text, options=["For all users", "For you only"], command=None, *args, **kw):
        super().__init__(parent, text=text, command=self._show_menu, *args, **kw)

        self.command = command
        self.options = options

        # Menu that appears on click
        self.menu = tk.Menu(self, tearoff=0)
        for label in options:
            self.menu.add_command(
                label=label,
                command=lambda opt=label: self._select(opt)
            )

    def _show_menu(self):
        # Position the menu right below the button
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.menu.tk_popup(x, y)
        self.menu.grab_release()

    def _select(self, option):
        if self.command:
            self.command(option)
            

if __name__ == "__main__":
    root = tk.Tk()
    root.title("ButtonGroup Demo")

    options = [
        ("Pizza", "pizza", "Delicious Italian pizza"),
        ("Pasta", "pasta", "Creamy pasta with cheese"),
        ("Salad", "salad", "Fresh green salad")
    ]

    def confirm_change(old, new):
        return messagebox.askyesno("Confirm", f"Switch from '{old}' to '{new}'?")

    group = ButtonGroup(
        root,
        options=options,
        #initial="pizza",
        command=confirm_change,
        tooltip_kwargs=dict(wraplength=200)
    )
    group.pack(padx=20, pady=20)
    
    def select_random():
        codes = [t[1] for t in options]
        choice = random.choice(codes)
        group.select(choice)
        root.after(1500, select_random)

    ttk.Button(root, text="Show Selection", command=lambda: messagebox.showinfo("Selection", f"Selected: {group.get()}")).pack(pady=10)
    
    select_random()

    root.mainloop()
