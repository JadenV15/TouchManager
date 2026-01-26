"""Indeterminate progress dialog"""
__all__ = ['Progress']

import tkinter as tk
from tkinter import ttk

class _Indeterminate(ttk.Progressbar):
    def __init__(self, parent, orient=tk.HORIZONTAL, length=300, mode='indeterminate', *args, **kw):
        super().__init__(parent, orient=orient, length=length, mode=mode, *args, **kw)
        
class Progress(tk.Toplevel):
    def __init__(self, parent, title='Progress', message='Loading', center=True, speed=10, lock=True, *args, **kw):
        self.parent = parent or tk._default_root
        assert self.parent
        super().__init__(parent, *args, **kw)
        
        self.title(title)
        self.resizable(False, False)
        
        if lock:
            self.protocol("WM_DELETE_WINDOW", lambda *_: None) # caller must manualy stop
        
        if center: # centre the (probably single-line) label
            self.message = tk.Label(self, text=message, justify='center', anchor='center')
        else:
            self.message = tk.Label(self, text=message, justify='left', anchor='left')
        self.message.pack(padx=5, pady=5)
        
        self.bar = _Indeterminate(self)
        self.bar.pack(padx=10, pady=10)
        
        self.bar.start(speed)
        
        self.lift(aboveThis=self.parent) # ?? needed
        self.focus_force()
        self.grab_set()
        # dont block
        
    def close(self):
        self.bar.stop()
        self.grab_release()
        self.destroy()
        
if  __name__ == '__main__':
    root = tk.Tk()
    Progress(root, lock=False)
    print('Hello')
    root.mainloop()