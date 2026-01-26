"""Device 'card' views on main view"""
__all__ = ['Card', 'TouchscreenCard', 'TouchpadCard']

import tkinter as tk
from tkinter import ttk
from contextlib import suppress

from touchdc.ui.elements.buttons import SystemButtonGroup
from touchdc.ui.elements.tooltip import Tooltip
from touchdc.ui.elements.progress import Progress
from .const import SHIELD
        
class Card(ttk.Frame):
    """Base class for a device card
    A simple frame with title bar, body and footer.
    """
    NAME = '<undefined>'
    
    def __init__(self, parent, title=None, relief=tk.RIDGE, padding=15, *args, **kw):
        super().__init__(parent, relief=relief, padding=padding, *args, **kw)
        self.root = tk._default_root
        self.parent = parent
        self.title = title or type(self).NAME.capitalize()
        self.name = type(self).NAME
        
        # The card stores its config in these variables (below). The controller can change these and then call refresh(), which pushes these values to the UI.
        
        # Tkinter StringVars (avoid the need for manual update by assigning a simple textvariable)
        self.variables = {
            'status': tk.StringVar(master=self, value=''),
            'note': tk.StringVar(master=self, value='')
        }
        
        # Plain text (some not updateable; may require manual updating of widgets)
        self.text = {
            'button_text': (SHIELD+'Enable', SHIELD+'Disable'),
            'tooltip_enable': f"Disable {self.name.lower()} using the default settings. View advanced settings for more details.", # wont update
            'tooltip_disable': f"Enable {self.name.lower()} using the default settings. View advanced settings for more details.", # wont update
            'tooltip_info': f"This status shows the current {self.name.lower()} state for you (the current user). If it doesn't match what you observe, you can try to reapply your setting to the device by clicking the selected button again, or by viewing the advanced settings for further adjustments.", # changeable
            'button_code': None # to change
        }
        
        # Function callbacks
        self.callbacks = { # changeable
            'status_change': lambda old, new: None
        }
        
        # draw after defining references to they have access to the references
        self._titlebar()
        self._body()
        self._footer()
        
    def _check_note(self):
        """Check if there's a note, if so, render it"""
        if self.variables.get('note').get():
            self.note.pack()
            self.note.pack()
            # Repeating it due to this article (not sure if true, but anyway, no harm done in trying): https://www.geeksforgeeks.org/python/python-winfo_ismapped-and-winfo_exist-in-tkinter/
        else:
            self.note.pack_forget()
        
    def _check_tooltip_info(self):
        """Check if there's an info tooltip, if so, render it"""
        if self.text.get('tooltip_info'):
            self.info.pack(side=tk.LEFT)
            self.info.pack(side=tk.LEFT)
            self.info_tooltip = Tooltip(self.info, text=self.text.get('tooltip_info'))
        else:
            self.info.pack_forget()
            self.info_tooltip.remove()
    
    def _titlebar(self):
        """Titlebar containing a title and info button"""
        self.titlebar = ttk.Frame(self)
        self.titlebar.pack(fill='x', expand=True, pady=5)
        
        self.titlebar.grid_columnconfigure(0, weight=0)
        self.titlebar.grid_columnconfigure(1, weight=1, minsize=100)
        self.titlebar.grid_columnconfigure(2, weight=0)
        
        ttk.Label(self.titlebar, text=self.title, font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky='w', padx=5)
        
        self.info_btn = ttk.Button(self.titlebar, text='Info')
        self.info_btn.grid(row=0, column=2, sticky='e', padx=5)
        
    def _body(self):
        """Body containing main toggle button"""
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True, pady=5)
        #self.body.pack_propagate(True)
        
        status_frame = ttk.Frame(self.body)
        status_frame.pack() # Cannot put fill='x', expand=True, because it must be centered horizontally and not expand (its children need to be centered too)
        
        ttk.Label(status_frame, text='Overall status: ').pack(side=tk.LEFT)
        ttk.Label(status_frame, textvariable=self.variables.get('status')).pack(side=tk.LEFT, padx=(0, 3))
        
        self.info = ttk.Label(status_frame, text='ⓘ')
        self.info_tooltip = Tooltip(self.info, text=self.text.get('tooltip_info'))
        self._check_tooltip_info()
        
        self.toggle = SystemButtonGroup(
            self.body,
            buttons=SystemButtonGroup.BTN2,
            button_text=self.text.get('button_text'),
            button_tips=(self.text.get('tooltip_enable'), self.text.get('tooltip_disable')),
            command=self.callbacks.get('status_change'),
            initial=None
        )
        self.toggle.pack(pady=5)
        
        self.note = ttk.Label(self.body, textvariable=self.variables.get('note'))
        self._check_note()
        
    def _footer(self):
        """Footer containing advanced and refresh buttons"""
        self.footer = ttk.Frame(self)
        self.footer.pack(fill='x', expand=True, pady=5)
        
        self.footer.grid_columnconfigure(0, weight=0)
        self.footer.grid_columnconfigure(1, weight=1, minsize=100)
        self.footer.grid_columnconfigure(2, weight=0)
        
        self.advanced_btn = ttk.Button(self.footer, text='Advanced')
        self.advanced_btn.grid(row=0, column=0, sticky='w', padx=5)
        
        self.refresh_cmd = lambda *_, **__: None
        self.refresh_btn = ttk.Button(self.footer, text='Refresh', command=self.refresh_cmd)
        self.refresh_btn.grid(row=0, column=2, sticky='e', padx=5)
    
    def _set_state(self, state=tk.DISABLED, widget=None):
        if widget is None:
            widget = self
        with suppress(tk.TclError): # Ignore containers that can't be disabled
                widget.configure(state=state)
        for child in widget.winfo_children():
            self._set_state(state=state, widget=child)
            
    def disable(self):
        """Disable the card by setting children to disabled"""
        self._set_state(state=tk.DISABLED, widget=self)
        
    def enable(self):
        """Enable the card"""
        self._set_state(state=tk.NORMAL, widget=self)
        
    def set_info_view(self, callback):
        """Controller hook for opening an info dialog"""
        self.info_btn.configure(command=callback)
    
    def set_advanced_view(self, callback):
        """Controller hook for opening an advanced dialog"""
        self.advanced_btn.configure(command=callback)
    
    def set_refresh(self, callback):
        """Controller hook to add refresh callback"""
        def magic():
            p = Progress(self.root)
            p.update_idletasks()
            
            def run():
                try:
                    callback()
                finally:
                    p.close()
            self.root.after(1, run)
        
        self.refresh_cmd = magic
        self.refresh_btn.configure(command=self.refresh_cmd)
    
    def refresh(self):
        """Update UI elements with refreshed data"""
        self.toggle.set(self.text.get('button_code'))
        self.toggle.command = self.callbacks.get('status_change')
        
        self._check_note()
        self._check_tooltip_info()
        
        self.root.position()

        
class TouchscreenCard(Card):
    """Touchscreen Card"""
    NAME = 'touchscreen'
    
class TouchpadCard(Card):
    """Touchpad Card"""
    NAME = 'touchpad'