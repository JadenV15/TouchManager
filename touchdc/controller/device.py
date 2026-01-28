"""CardController
Manages the 'device cards' (views for each device) in the main view
Launches child controllers for Info and Advanced views
"""

__all__ = ['CardController', 'TouchscreenController', 'TouchpadController']

import sys
import tkinter as tk
from contextlib import suppress
from functools import wraps
from typing import Optional, Union, Literal

from touchdc.utils.modal import *
from touchdc.ui.elements.progress import Progress
from touchdc.ui.view.secondary import *
from touchdc.system.pnp_errors import *
from touchdc.system.utils.shutdown import *
from .secondary import *
from .base import Base

class CardController(Base):
    """Base controller for a device 'card' """
    NAME = '<undefined>'
    
    # Defaults specifies what advanced actions to take when a button is pressed on the general device view
    DEFAULTS = { #placeholder
        'enable': {
            'device': True,
            'system': True,
            'user': True
        },
        'disable': {
            'device': False,
            'system': False,
            'user': False
        }
    }
    
    def __init__(self, model, view, name=None, root=None):
        super().__init__(model, view, name)
        assert self.root
        self.defaults = type(self).DEFAULTS # Default method of enabling/disaling
        
        if not self.model.device_exists:
            self.view.disable() # If device doesn't exist, grey out its view
            
        self.initialise() # Call Base.initialise
    
    def _info_view(self):
        """Launch an info window with its own controller"""
        self.info = InfoController(
            model=self.model,
            view=InfoView(
                parent=self.root,
                name=self.name
            ),
            name=self.name
        )
        
    def _advanced_view(self):
        """Launch an advanced window with its own controller"""
        self.advanced = AdvancedController(
            model=self.model,
            view=AdvancedView(
                parent=self.root,
                name=self.name
            ),
            name=self.name
        )
    
    def _bind_view(self):
        """Bind calllbacks to the view"""
        super()._bind_view()
        self.info = None
        self.advanced = None
        
        # Bind actions to buttons via view hooks
        self.view.set_info_view(self._info_view)
        self.view.set_advanced_view(self._advanced_view)
        
    def _confirm_change(self, old, new):
        """Confirm to change the status of a device"""
        assert old.lower() in self.model.STATES and new.lower() in self.model.STATES
        
        if old == new:
            return Ask.yesno(title='Confirm', message=f'Are you sure you want to re-{new.lower()} {self.name.lower()} with default settings?')
        else:
            context = self.name.capitalize()
            if old == self.model.ENABLE:
                context += f" is currently enabled."
            elif old == self.model.DISABLE:
                context += f" is currently disabled."
                
            return Ask.yesno(title='Confirm', message=f'{context} Are you sure you want to {new.lower()} {self.name.lower()}, using default settings?')
            
    def _success(self, new):
        """Display success message"""
        assert new.lower() in self.model.STATES
        
        return Info.showinfo(title='Success', message=f"Successfully {new.lower()}d {self.name.lower()}")
    
    
    
    @staticmethod
    def handle_error(func):
        """Decide what to do when an error occurs"""
        @wraps(func)
        def magic(*args, **kw):
            try:
                return func(*args, **kw)
            except DeviceInvalidOperationError:
                pass # operation not supported; ignore
            except DeviceOperationAbortedError:
                Error.aborted()  # show error message
                return False
            except DevicePermissionError:
                Error.access_denied() # show error message
                return False
            except Exception as e:
                raise
        return magic
        
    @handle_error
    def _model_toggle(self, options, mode):
        """Wrapper that decides what to do given an options dict (DEFAULTS) and a mode"""
        if mode == self.model.DEVICE:
            self.model.toggle(self._get_const(options.get('device')), self.model.DEVICE)
        elif mode == self.model.SYSTEM:
            self.model.toggle(self._get_const(options.get('system')), self.model.SYSTEM)
        elif mode == self.model.USER:
            self.model.toggle(self._get_const(options.get('user')), self.model.USER)
        return
    
    def toggle(self, old, new) -> Union[Literal[False], None]:
        """Change status from old to new"""
        if self._confirm_change(old, new):
            p = Progress(self.root)
            p.update_idletasks()
            
            try:
                options = self.defaults[new.lower()]
                for mode in self.model.MODES:
                    res = self._model_toggle(options, mode)
                    if res is False:
                        return False # Returning False reverts the ButtonGroup to its original selection
            finally:
                p.close() # Close the dialog
            
            # Success
            self._power(new)
            self._success(new)
        else:
            return False
        
    def refresh(self):
        """Refresh UI with new model data"""
        code = self._get_const(self.model.user_active)
        status = self._get_name(code)
        
        self.view.variables['status'].set(status)
        self.view.variables['note'].set('‾'*12)
        
        self.view.text['button_code'] = code
        
        self.view.callbacks['status_change'] = self.toggle
        
        self.view.refresh() # don't forget!
            
        
class TouchscreenController(CardController):
    """Touchscreen controller"""
    NAME = 'touchscreen'
    
    DEFAULTS = {
        'enable': {
            'device': True,
            'system': True,
            'user': None
        },
        'disable': {
            'device': False,
            'system': False,
            'user': None
        }
    }
    
        
class TouchpadController(CardController):
    """Touchpad controller"""
    NAME = 'touchpad'
    
    DEFAULTS = {
        'enable': {
            'device': True,
            'system': None, #doesnt exist
            'user': None
        },
        'disable': {
            'device': False,
            'system': None,
            'user': None
        }
    }
        
        
        