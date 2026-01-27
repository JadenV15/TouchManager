"""Main app view"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path
from importlib.resources import files
from typing import Optional, Union, List, Tuple

from touchdc._version import __version__
from touchdc.ui.utils.dpi import scale
from .cards import *

class Help(tk.Toplevel):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)
        
        self.parent = parent
        
        self.title('About')
        self.resizable(False, False)
        
        self.title_text = ttk.Label(self, text='Using Touch Manager', font=("Segoe UI", 12, "bold"), anchor='center')
        self.title_text.pack(fill='x', expand=True, pady=5)
        
        self.body = ttk.Frame(self, relief=tk.RIDGE, padding=15)
        self.body.pack(fill='x', expand=True, anchor='nw', padx=20, pady=20)
        
        self.text = ttk.Label(
            self.body,
            text="""Use the controls on the main page to toggle between Enabled (On) / Disabled (Off)
Used the controls on the advanced page to toggle advanced settings. Take caution when changing these settings.
Some actions have a shield icon beside them. These likely require administrator priveleges, and may prompt you with a UAC message.
Hover over a button or information icon (ⓘ) to get help about its function.
Enjoy!""",
            justify='center',
            wraplength=500
        )
        self.text.pack()
        
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(pady=15)
        
        close_btn = ttk.Button(self.btn_frame, text="Close", command=self.destroy)
        close_btn.pack(side=tk.LEFT)


class About(tk.Toplevel):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)
        
        self.parent = parent
        
        self.title('About')
        self.resizable(False, False)
        
        self.title_text = ttk.Label(self, text='Touch Device Manager', font=("Segoe UI", 12, "bold"), anchor='center')
        self.title_text.pack(fill='x', expand=True, pady=5)
        
        self.body = ttk.Frame(self, relief=tk.RIDGE, padding=15)
        self.body.pack(fill='x', expand=True, anchor='nw', padx=20, pady=20)
        
        self.text = ttk.Label(
            self.body,
            text=f"""A simple utility to manage your touch devices
Version: {__version__}
Authors: Jaden Chuah""",
            justify='center'
        )
        self.text.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(pady=15)
        
        close_btn = ttk.Button(self.btn_frame, text="Close", command=self.destroy)
        close_btn.pack(side=tk.LEFT)


class Menubar(tk.Menu):
    """Menu bar"""
    
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)
        
        self.parent = parent
        self.always_on_top = tk.BooleanVar(value=False)

        # File
        filemenu = tk.Menu(self, tearoff=0)
        filemenu.add_command(label="Exit", command=self.file_exit)
        self.add_cascade(label="File", menu=filemenu)

        # View
        viewmenu = tk.Menu(self, tearoff=0)
        zoom = tk.Menu(viewmenu, tearoff=0)
        zoom.add_command(label="Zoom In", command=self.zoom_in)
        zoom.add_command(label="Zoom Out", command=self.zoom_out)
        zoom.add_command(label="Restore Default Zoom", command=self.zoom_default)
        viewmenu.add_cascade(label="Zoom", menu=zoom)
        self.add_cascade(label="View", menu=viewmenu)

        # Help
        helpmenu = tk.Menu(self, tearoff=0)
        helpmenu.add_command(label="Help", command=self.show_help)
        helpmenu.add_command(label="About", command=self.show_about)
        self.add_cascade(label="Help", menu=helpmenu)
        
        # Options
        optionmenu = tk.Menu(self, tearoff=0)
        optionmenu.add_checkbutton(label="Always on top", onvalue=True, offvalue=False, variable=self.always_on_top, command=self.toggle_topmost)
        self.add_cascade(label="Options", menu=optionmenu)
    
    def file_exit(self):
        self.parent.destroy()
    
    def zoom(self, delta):
        self.parent.tk.call('tk', 'scaling', self.parent.current_scale+delta) # zoom wont listen
            
    def zoom_in(self):
        self.zoom(+0.2)
    
    def zoom_out(self):
        self.zoom(-0.2)
        
    def zoom_default(self):
        self.zoom(self.parent.default_scale)

    def show_help(self):
        Help(self.parent)

    def show_about(self):
        About(self.parent)
        
    def toggle_topmost(self):
        self.parent.wm_attributes('-topmost', bool(self.always_on_top.get()))


class App(tk.Tk):
    """Entry point"""
    
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.default_scale = self.tk.call('tk', 'scaling')

        self.draw()
        self.position()
    
    @property
    def current_scale(self):
        return self.tk.call('tk', 'scaling')
    
    def draw(self):
        # Setup
        self.withdraw()
        self.title("Touch Device Manager")
        
        #ico_path = files('touchdc.assets').joinpath('icon.png')
        ico_path = Path(__file__).resolve().parents[2] / 'assets' / 'icon.png'
        ico = Image.open(ico_path)
        photo = ImageTk.PhotoImage(ico)
        self.photo = photo
        self.wm_iconphoto(True, photo)
        #self.resizable(False, False)
        
        # Menu
        self.config(menu=Menubar(self))
        
        # Main area
        self.container = ttk.Frame(self, padding=20)
        self.container.pack(fill="both", expand=True)
        
        # Cards
        self.touchscreen = TouchscreenCard(self.container)
        self.touchpad = TouchpadCard(self.container)

        self.touchscreen.pack(fill="both", expand=True, pady=(0, 20))
        self.touchpad.pack(fill="both", expand=True)
    
    def position(self):
        self.update_idletasks()
        
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        
        self.wm_geometry(f"{width}x{height}+{x}+{y}") # use `wm_geometry` instead of `geometry` due to DPI awareness
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.deiconify()
    
    '''def _redraw(self):
        self.update_idletasks()
        for w in self.winfo_children():
            #w.update_idletasks()
            w.destroy()
        self.draw()
        self.position()
        self.update_idletasks()
        
        for c in [self.touchscreen, self.touchpad]:
            c.refresh_cmd()
            
    def redraw(self):
        self.after(10, self._redraw)''' # Forget about zoom - is hell

if __name__ == "__main__":
    app = App()
    app.mainloop()
