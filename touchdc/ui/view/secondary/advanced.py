"""Advanced View
Device-specific views built on composition, not inheritance (todo: make this consistent)
"""

import tkinter as tk
from tkinter import ttk
from contextlib import suppress

from touchdc.ui.elements.buttons import SystemButtonGroup
from touchdc.ui.elements.tooltip import Tooltip
from touchdc.ui.view.const import SHIELD

class Row:
    """Class that defines a row of elements to toggle a given mode"""
    def __init__(self, parent, row, name, btn=SystemButtonGroup.BTN2, disable=False, text=None, padx=7, pady=5, x_expand=True):
        self.parent = parent
        self.row = row
        self.name = name
        self.btn = btn
        self.disable_on = disable
        self.padx = padx
        self.pady = pady
        self.x_expand = x_expand
        
        self.widgets = [] # Keep track of widgets
        
        # The row stores its config in these variables (below). The controller can change these
        
        self.variables = {
            'status': tk.StringVar(master=self.parent, value='')
        }
        
        text = text or {}
        self.text = {
            'button_text': None,
            'tooltip_enable': None,
            'tooltip_disable': None,
            'tooltip_none': None,
            'tooltip_info': None,
            'button_code': None,
            **text
        }
        
        self.callbacks = {
            'status_change': lambda old, new: None
        }
        
    def _check_tooltip_info(self):
        """Check if there's an info tooltip, if so, render it"""
        if self.text.get('tooltip_info'):
            self.info.grid(row=self.row, column=3, padx=self.padx, pady=self.pady)
            self.info.grid(row=self.row, column=3, padx=self.padx, pady=self.pady)
            self.info_tooltip = Tooltip(self.info, text=self.text.get('tooltip_info'))
        else:
            self.info.grid_forget()
            self.info_tooltip.remove()
    
    def show(self):
        """Draw the row"""
        if self.x_expand:
            self.parent.columnconfigure(0, weight=1)
            self.parent.columnconfigure(1, weight=1)
            self.parent.columnconfigure(2, weight=1)
            self.parent.columnconfigure(3, weight=1)
        
        # Left label
        lbl = ttk.Label(self.parent, text=self.name)
        lbl.grid(row=self.row, column=0, sticky="w", padx=self.padx, pady=self.pady)
        self.widgets.append(lbl)

        # Status value
        self.value = ttk.Label(self.parent, textvariable=self.variables.get('status'))
        self.value.grid(row=self.row, column=1, sticky="w", padx=self.padx, pady=self.pady)
        self.widgets.append(self.value)

        # Action button
        self.toggle = SystemButtonGroup(
            self.parent,
            buttons=self.btn,
            button_text=self.text.get('button_text'),
            button_tips=(self.text.get('tooltip_enable'), self.text.get('tooltip_disable'), self.text.get('tooltip_none'))[:len(self.btn)],
            command=self.callbacks.get('status_change'),
            initial=None
        )
        self.toggle.grid(row=self.row, column=2, padx=self.padx, pady=self.pady)
        self.widgets.append(self.toggle)

        # Info / help label
        self.info = ttk.Label(self.parent, text='ⓘ')
        self.info_tooltip = Tooltip(self.info, text=self.text.get('tooltip_info'))
        self.widgets.append(self.info)
        self._check_tooltip_info()
            
        if self.disable_on:
            self.disable()
            
    def disable(self):
        """Disable the row's widgets"""
        for w in self.widgets:
            with suppress(tk.TclError):
                w.configure(state='disabled')
                
    def enable(self):
        """Enable the row's widgets"""
        for w in self.widgets:
            with suppress(tk.TclError):
                w.configure(state='normal')
                    
    def refresh(self):
        """Refresh all widgets with updated data"""
        self.toggle.set(self.text.get('button_code'))
        self.toggle.command = self.callbacks.get('status_change')
            
        self._check_tooltip_info()
        

class AdvancedView(tk.Toplevel):
    """Advanced view containing three toggle rows"""
    NAME = '<undefined>'
    
    def __init__(self, parent, name=None):
        super().__init__(parent)
        self.parent = parent
        self.name = name or type(self).NAME
        
        self._draw()
        
    def _draw(self):
        self.title(f"Advanced - {self.name.capitalize()}")
        self.resizable(False, False)

        # Todo: proper flashing modal
        self.transient(self.parent)
        self.grab_set()

        self.toggle_frame = ttk.Frame(self, relief=tk.RIDGE, padding=15)
        self.toggle_frame.pack(fill='x', expand=True, anchor='nw', padx=20, pady=20)

        self.device_row = Row(
            self.toggle_frame,
            0,
            'Hardware status:',
            btn=SystemButtonGroup.BTN2,
            text={
                'button_text': (SHIELD+'Enable', SHIELD+'Disable'),
                'tooltip_enable': f"Enable {self.name.lower()} at the device level",
                'tooltip_disable': f"Disable {self.name.lower()} at the device level",
                'tooltip_info': f"This is the highest level of control of the {self.name.lower()}, which interacts with the plug and play device. Administrator privileges may be required. If this is set to 'disabled', none of the below settings will have any effect."
            }
        )
        self.system_row = Row(
            self.toggle_frame,
            1,
            'System status:',
            btn=SystemButtonGroup.BTN3,
            text={
                'button_text': (SHIELD+'Enable', SHIELD+'Disable', SHIELD+'None'),
                'tooltip_enable': f"Enable {self.name.lower()} for all users",
                'tooltip_disable': f"Disable {self.name.lower()} for all users",
                'tooltip_none': f"Remove any {self.name.lower()} settings that apply to all users",
                'tooltip_info': f"This specifies settings that should apply to all users of this computer (or just you, if you are the sole user). If the above is enabled, this has the option to disable {self.name.lower()}."
            }
        )
        self.user_row = Row(
            self.toggle_frame,
            2,
            'User status:',
            btn=SystemButtonGroup.BTN3,
            text={
                'button_text': ('Enable', 'Disable', 'None'),
                'tooltip_enable': f"Enable {self.name.lower()} for you (the current logged-on user)",
                'tooltip_disable': f"Disable {self.name.lower()} for you (the current logged-on user)",
                'tooltip_none': f"Remove any {self.name.lower()} settings that apply to you (the current logged-on user)",
                'tooltip_info': f"This specifies settings that should apply to you only, and takes precendence (and can override) the above 'system' setting. For example (on a computer with many users), it is possible to disable {self.name.lower()} for everyone except a few, by turning the above setting to disabled, then logging in as those users and enabling this setting."
            }
        )
        self.rows = [self.device_row, self.system_row, self.user_row] # don't change the order
        
        for r in self.rows:
            r.show()

        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(pady=15)
        
        close_btn = ttk.Button(self.btn_frame, text="Close", command=self.destroy)
        close_btn.pack(side=tk.LEFT)
    
    def set_refresh(self, callback):
        """Controller hook to add refresh callback"""
        pass
    
    def refresh(self):
        """Refresh widgets"""
        for r in self.rows:
            r.refresh()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("300x200")

    ttk.Button(root, text="Open Advanced Dialog",
               command=lambda: AdvancedView(root)).pack(padx=10, pady=10)

    root.mainloop()
