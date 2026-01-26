"""AppController
The main controller in charge of the root Tk window
Launches child controllers
"""

from touchdc.system.model import *
from .device import *

class AppController:
    def __init__(self, view):
        self.view = view
        
        self.touchscreen = TouchscreenController(
            model=Touchscreen(),
            view=self.view.touchscreen,
            root=self.view
        )
        
        self.touchpad = TouchpadController(
            model=Touchpad(),
            view=self.view.touchpad,
            root=self.view
        )
    
    def run(self):
        self.view.mainloop()