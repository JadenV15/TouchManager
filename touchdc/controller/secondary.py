"""Controllers for popup views
Built by composition not inheritance (todo: be consistent with device.py)
"""

__all__ = ['AdvancedController', 'InfoController']

import sys
from touchdc.utils.modal import *
from touchdc.ui.elements.progress import Progress
from touchdc.system.pnp_errors import *
from touchdc.system.utils.shutdown import *
from .base import Base

class AdvancedController(Base):
    """Generic controller for Advanced dialogs"""
    NAME = '<undefined>'
    
    def __init__(self, model, view, name, root=None):
        super().__init__(model, view, name)
        assert self.root
        
        self.initialise()
        
    def _confirm_change(self, mode, old, new):
        """Confirm to change the status of a device"""
        assert old.lower() in self.model.STATES and new.lower() in self.model.STATES
        
        if old == new:
            if new == self.model.NONE:
                return Ask.yesno(title='Confirm', message=f"Are you sure you want to re-clear the {mode.capitalize()} status of {self.name.lower()} to None?")
            else:
                return Ask.yesno(title='Confirm', message=f'Are you sure you want to re-{new.lower()} the {mode.capitalize()} status of {self.name.lower()}?')
        else:
            if old == self.model.NONE:
                context = f"The {mode.capitalize()} status of {self.name.lower()} is currently empty (doesn't exist)."
            else:
                context = f"The {mode.capitalize()} status of {self.name.lower()} is currently {old.lower()}d."
            return Ask.yesno(title='Confirm', message=f'{context} Are you sure you want to set that status to {new.lower()}?', parent=self.view)
            
    def _success(self, new):
        """Display success message"""
        assert new.lower() in self.model.STATES
        
        action = new.lower()+'d' if new in (self.model.ENABLE, self.model.DISABLE) else 'cleared'
        return Info.showinfo(title='Success', message=f"Successfully {action}", parent=self.view)
    
    def toggle(self, mode, old, new):
        """Change status from old to new"""
        if self._confirm_change(mode, old, new):
            p = Progress(self.root)
            p.update_idletasks()
            
            try:
                self.model.toggle(new, mode)
            except DeviceInvalidOperationError:
                pass # the buttons should be disabled anyway if no such operation
            except DeviceOperationAbortedError:
                Error.aborted()
                return False
            except DevicePermissionError:
                Error.access_denied()
                return False
            except Exception as e:
                raise
            finally:
                p.close()
                
            if mode in [self.model.SYSTEM, self.model.USER]: # Only registry keys require signout/restart
                self._power(new)
        else:
            return False
        self._success(new)
        
    def refresh(self):
        """Refresh ui with new model data"""
        for mode, row in zip(list(self.model.MODES), list(self.view.rows)):
            try:
                code = self._get_const(getattr(self.model, f"{mode.lower()}_enabled")) # eg. Device.device_enabled -> Device.ENABLE
                status = self._get_name(code)
            except NotImplementedError: # No such attribute - not supported; disable and move on
                row.disable()
                continue
            
            row.variables['status'].set(status)
            
            row.text['button_code'] = code
            
            row.callbacks['status_change'] = lambda old, new, mode=mode: self.toggle(mode, old, new) # careful of late closures
            
        self.view.refresh()
            

class InfoController(Base):
    """Generic controller for Device info dialogs"""
    NAME = '<undefined>'
    
    def __init__(self, model, view, name, root=None):
        super().__init__(model, view, name)
        
        # Tooltips that describe fields of data
        self.descriptions = {
            'Instance ID': 'The device instance\'s unique ID',
            'Device Description': 'Description of the device',
            'Status': 'Current status of the device. Possible values: Started / stopped / disconnected / disabled / problem / unknown',
            'Driver Name': 'The name of the device\'s hardware driver'
        }
        
        self.initialise()
        
    def refresh(self):
        """Update the UI with new field data"""
        self.view.fields = [
            (key, val, self.descriptions.get(key))
            for key, val in self.model.get_device().items()
        ]
        
        self.view.refresh()