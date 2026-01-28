"""Controller template
Outlines interactions with model/view
Small helpers
"""
__all__ = ['Base']

import tkinter as tk
from abc import ABC, abstractmethod

from touchdc.utils.observe import Observer

class Base(ABC):
    """Base controller for a device 'card' """
    NAME = '<undefined>'
    
    @abstractmethod
    def __init__(self, model, view, name=None, root=None):
        self.model = model
        self.view = view
        
        self.name = name or type(self).NAME
        self.root = root or tk._default_root
        
        # Subclass: call super() init then do custom setup, then call self.initialise
    
    def initialise(self): # initialise, mind, not initialize
        """Setup the view"""
        self._bind_view()
        
        self.root.update_idletasks()
        self.root.after(1, self.refresh)
    
    def _bind_view(self):
        """Bind callbacks to the view
        Allows refreshing of the view
        """
        def dispose(event):
            # Triggers on window deletion
            if event.widget is self.view:
                self.model.detach(self.listener)
                self.listener = None
                self.view = None
        
        if callable(getattr(self.view, 'set_refresh', None)): # Bind to refresh button via view hook
            self.view.set_refresh(self.refresh)
            
        parent = self
        # Observer that is notified of change and refreshes
        class Listener(Observer):
            def update(self, observable):
                parent.refresh()
        self.listener = Listener()
        self.model.attach(self.listener)
        
        # NOTE: binding to <Destroy> binds to every widget in the window including the window, meaning the function will fire many times
        self.view.bind('<Destroy>', dispose) 
    
    def _get_const(self, val):
        """Conversion helper
        Converts boolean values into their respective Device action constants
        """
        if val is True:
            return self.model.ENABLE
        elif val is False:
            return self.model.DISABLE
        elif val is None:
            return self.model.NONE
        else:
            raise ValueError(f"Unexpected value: {val}")
            
    def _get_name(self, const):
        """Convert Device state constant to a status display string, eg. 'Enabled' """
        if const in (self.model.ENABLE, self.model.DISABLE):
            return const.capitalize() + 'd'
        elif const == self.model.NONE:
            return const.capitalize()
            
    def _power(self, new):
        """Display power options dialog(after successfully updating status)"""
        res = Ask.button_option(
            parent=self.root,
            title='Power',
            message=f"The computer may need to restart or sign out to complete the operation. Please save your work before proceeding.\nIf you notice {self.name.lower()} is already {new+'d'}, you can ignore this message.",
            options=[
                ('Sign out', 'signout'),
                ('Restart', 'restart'),
                ('Later', 'later')
            ],
            default='signout'
        )
        
        if res == 'signout':
            logoff()
        elif res == 'restart':
            restart()
        elif res == 'later' or res is False: # Closed window
            pass
    
    @abstractmethod
    def refresh(self):
        """Refresh UI with new model data"""
        # Update view variables here
        
        self.view.refresh() # Call the view's refresh method
        