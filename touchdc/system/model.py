"""Model for manipulation of plug-and-play devices on Windows"""

'''Note: devices can be manipulated via powershell cmdlets or pnputil. For simplicity the latter method is used

Get-PnpDevice | Where-Object {$_.FriendlyName -like '*touch screen*'} | Disable-PnpDevice -Confirm:$false
Get-PnpDevice | Where-Object {$_.FriendlyName -like '*touch screen*'} | Enable-PnpDevice -Confirm:$false

pnputil /enum-devices /class HIDClass
pnputil /disable-device <Instance ID>
pnputil /enable-device <Instance ID>

In general, devices can be enabled/disabled at the device level, or through the Registry.
'''

__all__ = ['Device', 'Touchscreen', 'Touchpad']

# NOTE: pnputil only included in Vista and later

import subprocess
import platform
import tempfile
import os
from abc import ABC, abstractmethod
from typing import Union, Optional, Literal, Any
from functools import wraps

from touchdc.utils.observe import *
from touchdc.utils.modal import Ask
from .command import Run, Reg, cmd_errors, reg_errors
from .pnp_errors import *

class Device(Observable):
    """A base class for PnP devices"""
    # Possible states and modes
    DEVICE  = 'device' # Refers to the device instance
    SYSTEM  = 'system' # Refers to the system registry key (if any)
    USER    = 'user' # Refers to the user registry key (if any)
    
    MODES   = (DEVICE, SYSTEM, USER)
    
    DISABLE = 'disable'
    ENABLE  = 'enable'
    NONE    = 'none' # (Registry) Not set
    
    STATES  = (DISABLE, ENABLE, NONE)
    
    # Pnputil possible statuses
    STATUS_UNKNOWN       = 'unknown'
    
    STATUS_PROBLEM       = 'problem'
    
    STATUS_STARTED       = 'started'
    STATUS_STOPPED       = 'stopped'
    
    STATUS_DISABLED      = 'disabled'
    STATUS_DISCONNECTED  = 'disconnected'
    
    # Registry values for toggling devices - format: (key_path, value_name, reg_type [as int])
    SYSTEM_KEY = ('', '', 0)
    USER_KEY   = ('', '', 0)
    
    # Names
    NAME = '<undefined>'
    DEVICE_NAMES = [] # Identifiers used to find the device from a pnputil list
    
    def __init__(self):
        super().__init__()
        self.cls = type(self) # shorthand
    
    @staticmethod
    def handle_error(func):
        """Handles errors that may occur during operation
        Takes errors generated from lower utils such as Run and Reg, and wraps them in the model's own errors, to be propogated to a higher-level entity (i.e. controller)
        """
        @wraps(func)
        def magic(*args, **kw):
            try:
                return func(*args, **kw)
            except (cmd_errors.UserAbortedError, reg_errors.RegistryOperationAbortedError) as e:
                raise DeviceOperationAbortedError(f"Registry operation was aborted by the user") from e
            except (cmd_errors.AccessDeniedError, reg_errors.RegistryPermissionError) as e:
                raise DevicePermissionError(f"Not enough permissions to complete the registry operation") from e
        return magic
    
    @handle_error
    def get_device(self, names: Optional[Union[list[str], str]] = None, get_all=False, elevate=False, auto_elevate=True) -> Union[dict, list[dict]]:
        """Get the properties of HIDClass devices via pnputil.
        Args:
            names: provide a name or list of names to match one device. If this is not spedified, default to the class DEVICE_NAMES.
            get_all: if True, ignore `names` and return a list of dicts representing all HIDClass devices
        Returns:
            Dict of device fields or list of dicts.
        Raises:
            PnpError: pnp-related domain error
        """
        
        '''Note regarding pnputil
        
        The possible status strings listed by `pnputil /enable-devices` (as far as I know) are:
        
        disabled: device instance disabled. Done through `pnputil /disable-device`. Not to be confused with driver-level operations such as `/delete-driver` 
        disconnected: device not physically connected. Driver is installed and Windows recognises the device, but cannot interact with it until it is reconnected.
        stopped: device is connected, but its driver is not loaded or running. May happen due to a problem (e.g. the driver shuts down the device) or OS (e.g. low power mode, conserve power) or start on demand (start type where driver only runs when needed)
        started: device is running.
        problem: an error occurred that prevents normal functioning of the device. See error codes: https://support.microsoft.com/en-us/topic/error-codes-in-device-manager-in-windows-524e9e89-4dee-8883-0afa-6bca0456324e
        
        There is no 'connected' status; `pnputil /enum-devices /connected` yields those that are 'started'.
        '''
        
        if names is None:
            names = self.cls.DEVICE_NAMES # Default to the class names
        if isinstance(names, str):
            names = [names]
        
        # Unelevated users can see most device data, but allow elevation for the sake of consistency
        rc, out, err = Run.run_ps("pnputil /enum-devices /class HIDClass", elevate=elevate, auto_elevate=False)
        output = (out+'\n'+err).lower().strip()
        try:
            check_error(output)
        except DevicePermissionError as e:
            if auto_elevate and not elevate:
                if Ask.elevate():
                    return self.get_device(names=names, get_all=get_all, elevate=True)
                else:
                    raise DeviceOperationAbortedError("Elevation cancelled by user") from e
            else:
                raise
        
        _blocks = out.split('\n\n') # Raw blank-line-separated "blocks". Top block is likely "Microsoft PnP Utility"
        blocks = [] # Dictionary-organised blocks
        for b in _blocks:
            if any([n.lower() in b.lower() for n in names]) and ':' in b: # filter the blocks we are looking for
                blocks.append({})
                for l in b.splitlines(): # split block into field-value pairs
                    if ':' in l:
                        k, v = l.split(':', 1)
                        blocks[-1][k.strip()] = v.strip()
        
        if get_all:
            return blocks # Return list of all dicts
        
        if len(blocks) != 1:
            raise DeviceNotFoundError(f"Could not find device: {len(blocks)} HIDClass device(s) found that meet the criteria")
        else:
            return blocks[0] # dict of the device
    
    def get_field(self, field='Status', strict=True, names: Optional[Union[list[str], str]] = None) -> Union[str, None]:
        """Extract a field from get_device() output.
        Args:
            field: name of the field to retrieve, by default 'Status'.
            strict: whether to raise an exception if the field cannot be found, or return None.
            names: provide a name or list of names to match one device. If this is not spedified, default to the class DEVICE_NAMES.
        Returns:
            str: if the value was found
            None: if the value could not be found (strict=False)
        """
        device = self.get_device(names)
        
        value = device.get(field.capitalize())
        if value is None:
            if strict:
                raise DevicePropertyNotFoundError(f"Value '{field}' not found in device: '{device}'")
            
        return value
    
    @property
    def device_exists(self) -> bool:
        """Check if the device can be found"""
        # always check this proeprty to ensure the device actually exists!
        try:
            device = self.get_device()
        except DeviceNotFoundError:
            return False
        else:
            return True
    
    @property
    def device_enabled(self) -> bool:
        """Check if the device is enabled"""
        status = self.get_field()
        
        if status.lower() == 'disabled':
            return False
            
        return True
        
    @property
    def device_running(self) -> bool:
        """Check if the device is running"""
        # note: this doesn't necessarily mean (?) its running for the current user
        status = self.get_field()
        
        if status.lower() == 'started':
            return True
        
        return False
        
    @property
    def device_working(self) -> bool:
        """Check that the device works without problems"""
        status = self.get_field()
        
        if status.lower() == 'problem':
            return False
            
        return True
        
    def get_problem(self) -> tuple[Union[str, None], Union[str, None]]:
        """Get the problem code and status if there is a problem with the device"""
        prob_code = self.get_field('Problem Code', strict=False)
        prob_status = self.get_field('Problem Status', strict=False)
        
        return prob_code, prob_status
    
    @handle_error
    def _check_key(self, key) -> Union[bool, None]:
        """Check whether a given registry value is True, False or None, based on its data.
        Args:
            key: a tuple (key_path, value_name, reg_type)
        Returns:
            bool or None
        """
        # If no value exists (None), then there will be no per-level overrides, and the next level up has the say
        
        path, name, type_ = key
        try:
            reg_val, reg_type = Reg.get_reg(path, name)
        except reg_errors.RegistryItemNotFoundError:
            return None # Item doesn't exist
        
        if Reg.normalise(reg_type) != Reg.normalise(type_):
            return None # Type doesn't match
            
        if reg_val == 0:#in ('0', 0):    - not needed; get_reg returns correct type
            return False
        elif reg_val == 1:
            return True
            
        return None # Unknown value
    
    @property
    def system_enabled(self) -> Union[bool, None]:
        """Check whether the system (hklm) registry enables the device"""
        return self._check_key(self.cls.SYSTEM_KEY)
    
    @property
    def user_enabled(self) -> Union[bool, None]:
        """Check whether the user (hkcu) registry enables the device"""
        return self._check_key(self.cls.USER_KEY)
        
    @property
    def user_active(self) -> bool:
        """Check whether the device is on or not from the current user's perspective"""
        if not self.device_enabled: # Device disabled, cannot run
            return False
        else: # Enabled
            try:
                if self.system_enabled in (True, None): # Also Enabled`
                    if self.user_enabled is False:
                        return False
                    else: # True, None (Also Enabled)
                        return True
                else: # False
                    if self.user_enabled in (False, None):
                        return False
                    else: # True
                        return True
            except NotImplementedError: # There is no system key (touchpad)
                if self.user_enabled is False:
                    return False
                else: # True, None
                    return True
        
        raise RuntimeError(f"Failed to get user active status")
    
    def _check(self, state=None, mode=None):
        # Check that the arguments are valid
        if state is not None:
            assert state in (self.cls.ENABLE, self.cls.DISABLE, self.cls.NONE)
        if mode is not None:
            assert mode in (self.cls.DEVICE, self.cls.SYSTEM, self.cls.USER)
            if mode == self.cls.DEVICE and state is not None:
                assert state != self.cls.NONE # Device is either En. or Dis.
    
    @handle_error
    def _toggle(self, state, mode, elevate=False, auto_elevate=True) -> None:
        """Set a state and a mode for the device. Once set, notify all observers of the update. """
        
        try:
            self._check(state, mode)
        except (AssertionError, NotImplementedError) as e:
            raise DeviceInvalidOperationError(f"Bad arguments: '{state}' '{mode}'") from e
        
        if mode == self.cls.DEVICE:
            instance_id = self.get_device()['Instance ID']
            
            rc, out, err = Run.run_ps(f"pnputil /{state}-device \"{instance_id}\"", elevate=elevate, auto_elevate=False)
            out = out.lower().strip()
            err = err.lower().strip()
            output = out+'\n'+err
            
            if out or err:
                try:
                    check_error(output)
                except DevicePermissionError as e:
                    if auto_elevate and not elevate:
                        if Ask.elevate():
                            return self._toggle(state, mode, elevate=True) # let run_ps handle elevation
                        else:
                            raise DeviceOperationAbortedError("Elevation cancelled by user") from e
                    else:
                        raise
                except DevicePropertyExistsError:
                    return # Device already enabled/disabled, nothing to do
            
            # Note: pnputil does not validate the instance id. If an invalid id like "HELLO" is used when disabling (or enabling), output is 'Microsoft PnP Utility\n\n' (silent failure). Whereas with a valid id, the output is 'Microsoft PnP Utility\n\nDisabling device:     <id>\nDevice disabled successfully.\n\n'. Thus we check that 'success' is in the output.
            if 'success' in output:
                return
            else:
                raise PnpError(f"Failed to {state.capitalize()} device with instance id '{instance_id}'. Stdout: '{out}'\nStderr: '{err}'")
        
        else:
            if mode == self.cls.SYSTEM:
                path, name, reg_type = self.cls.SYSTEM_KEY
            elif mode == self.cls.USER:
                path, name, reg_type = self.cls.USER_KEY
                
            if state == self.cls.DISABLE:
                Reg.set_reg(path, name, 0, reg_type)
            elif state == self.cls.ENABLE:
                Reg.set_reg(path, name, 1, reg_type)
            elif state == self.cls.NONE:
                if Reg.test_reg(path, name):
                    Reg.del_reg(path, name)
    
    # The _toggle method may call itself, triggering a refresh halfway through the operation. It's safer to decorate a wrapper which runs only once.
    @Observable.observed 
    def toggle(self, *args, **kw) -> None:
        self._toggle(*args, **kw)
    
    # === optional wrappers ===
    
    def disable(self, mode):
        return self.toggle(self.cls.DISABLE, mode)
    
    def enable(self, mode):
        return self.toggle(self.cls.ENABLE, mode)
    
    def clear(self, mode):
        return self.toggle(self.cls.NONE, mode)
    
    # ========================
    
    def reset(self):
        # TODO - toggle twice? or reset customisation settings?
        pass
        
    def open(self):
        # TODO - open system dialog
        pass

# Note: 4 corresponds to DWord
# TODO: improve possible DEVICE_NAMES for better location of devices - maybe add regexes

class Touchscreen(Device):
    """Touchscreen model"""
    SYSTEM_KEY = (r"HKLM:\SOFTWARE\Microsoft\Wisp\Touch", 'TouchGate', 4)
    USER_KEY   = (r"HKCU:\SOFTWARE\Microsoft\Wisp\Touch", 'TouchGate', 4)
    
    NAME = 'touchscreen'
    DEVICE_NAMES = ['touch screen', 'touchscreen']
    
class Touchpad(Device):
    """Touchpad model"""
    SYSTEM_KEY = ()
    USER_KEY   = (r"HKCU:\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchPad\Status", 'Enabled', 4)
    
    NAME = 'touchpad'
    DEVICE_NAMES = ['touch pad', 'touchpad']
    
    @property
    def system_enabled(self):
        raise NotImplementedError("No system key") # accessing a nonexistent property - use NotImplementedError rather than DeviceInvalidOperationError
        
    def _check(self, state=None, mode=None):
        super()._check(state, mode)
        if mode == self.cls.SYSTEM: # There is no system key
            raise NotImplementedError("No system key")


if __name__ == '__main__':
    pass