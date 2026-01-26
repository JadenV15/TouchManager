"""Info View
Device-specific views built on composition, not inheritance (todo: make this consistent)
"""

import tkinter as tk
from tkinter import ttk

from touchdc.ui.elements.tooltip import Tooltip

class Row:
    """Class that defines a row containing a single field (entry)"""
    def __init__(self, parent, row, field_name, field_value, tip=None, disable=False, padx=10, pady=3, x_expand=True):
        self.parent = parent
        self.row = row
        self.name = field_name
        self.value_var = field_value if isinstance(field_value, tk.StringVar) else tk.StringVar(master=parent, value=field_value) # use a stringvar for easy updating
        self.tip = tip
        self.disable = disable
        self.padx = padx
        self.pady = pady
        self.x_expand = x_expand
        
        self.widgets = []
    
    def show(self):
        """Draw the row"""
        if self.x_expand:
            self.parent.columnconfigure(0, weight=1)
            self.parent.columnconfigure(1, weight=1)
            self.parent.columnconfigure(2, weight=1)
        
        # Left label
        lbl = ttk.Label(self.parent, text=self.name)
        lbl.grid(row=self.row, column=0, sticky="w", padx=self.padx, pady=self.pady)
        self.widgets.append(lbl)

        # Help label
        if self.tip:
            self.tip_label = ttk.Label(self.parent, text="ⓘ")
            self.tip_label.grid(row=self.row, column=1, padx=(0, self.padx), pady=self.pady)
            self.widgets.append(self.tip_label)
            self.tip_tooltip = Tooltip(self.tip_label, text=self.tip)

        # Field
        self.entry = ttk.Entry(self.parent, textvariable=self.value_var, state='readonly', width=25)
        self.entry.grid(row=self.row, column=2, sticky="e", padx=self.padx, pady=self.pady)
        self.entry.bind("<FocusIn>", lambda e, ent=self.entry: ent.select_range(0, 'end'))
        self.widgets.append(self.entry)
            
        if self.disable:
            for w in self.widgets:
                with suppress(tk.TclError):
                    w.configure(state='disable')

class InfoView(tk.Toplevel):
    """Info view for displaying device fields"""
    NAME = '<undefined>'
    
    def __init__(self, parent, fields=None, name=None):
        """
        fields: list of tuples (field_name, value) where value is a stringvar
        """
        super().__init__(parent)
        self.parent = parent
        self.name = name or type(self).NAME
        self.fields = fields or [('', '')]
        
        self.title(f"Info - {self.name.capitalize()}")
        self.resizable(False, False)

        # Make it modal
        self.transient(parent)
        self.grab_set()

        # Frame for layout - keep consistent 15, 20 padding across most frames in the app
        self.info_frame = ttk.Frame(self, relief=tk.RIDGE, padding=15) # inner padding (same as ipadx, ipady in .pack() - see https://stackoverflow.com/questions/77781579/python-tkinter-what-is-the-difference-between-a-widgets-padx-and-pack-methods)
        self.info_frame.pack(fill='x', expand=True, anchor='nw', padx=20, pady=20) # outer padding
        
        self.rows = []
        for row, (field_name, field_value, *other) in enumerate(self.fields):
            r = Row(self.info_frame, row, field_name, field_value, tip=other[0] if other else None)
            self.rows.append(r)
            r.show()
        
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(pady=15)
        
        close_btn = ttk.Button(self.btn_frame, text="Close", command=self.destroy)
        close_btn.pack(side=tk.LEFT)
    
    def set_fields(self, fields):
        """Controller hook to update field data"""
        self.fields = fields
    
    def set_refresh(self, callback):
        """Controller hook to add refresh callback"""
        pass
    
    def refresh(self):
        """Refresh UI with updated data"""
        # todo: test
        for r in self.rows:
            for w in r.widgets:
                w.destroy()
        
        for row, (field_name, field_value, *other) in enumerate(self.fields):
            r = Row(self.info_frame, row, field_name, field_value, tip=other[0] if other else None)
            self.rows.append(r)
            r.show()

# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x200")

    fields = [
        ("Field 1", "Value 1", "A description"),
        ("Field 2", "Value 2"),
        ("Field 3", "Value 3"),
    ]

    ttk.Button(root, text="Show Info", command=lambda: InfoView(root, fields)).pack(pady=50)

    root.mainloop()
