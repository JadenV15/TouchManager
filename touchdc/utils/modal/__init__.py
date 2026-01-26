"""A small util for creating simple user modals.
Callers using this package remain 'dumb' and never need to know how the dialog is generated (e.g. through tkinter)
Supports GUI and CLI (just a proof of concept) modes
"""

from .ui import *
from . import setting