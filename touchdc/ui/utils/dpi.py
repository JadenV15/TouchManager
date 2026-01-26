"""DPI aware tkinter
Import into all GUI scripts
"""

from hidpi_tk import DPIAwareTk
import tkinter as tk
import ctypes

tk.Tk = DPIAwareTk

# hidpi_tk sets value of 2, but this causes hugely enlarged ui when window dragged to another monitor.
# Setting to 1 prevents this but has the caveat of introducing slight blur.
ctypes.windll.shcore.SetProcessDpiAwareness(1)

def scale(x):
    """Scale text and images properly in DPI-aware tkinter
    Returns the scaled measurement
    """
    root = tk._default_root
    if root is None:
        return
    return int(root.tk.call('tk', 'scaling')*x)