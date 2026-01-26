"""Pnp errors, for pnputil"""

from touchdc.errors import AppError # Base Error

# Generic Pnp error
class PnpError(AppError): pass

# No such device
class DeviceNotFoundError(PnpError): pass

# No such device property (eg. no Problem code)
class DevicePropertyNotFoundError(PnpError): pass

# Attempted to set a device state that has already been set (eg. Enabling twice)
# Usually code 50 (tested), see https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-
class DevicePropertyExistsError(PnpError): pass 

# Not enough permissions
class DevicePermissionError(PnpError): pass

# No such operation (eg. Device.NONE not applicable for pnputil
class DeviceInvalidOperationError(PnpError): pass

# Operation cancelled by user (eg. UAC cancelled)
class DeviceOperationAbortedError(PnpError): pass


# Below is some short code to check which (if any) exception to raise, given raw powershell output from Run.

import re
from typing import Union, Optional

ERROR_MAP = {
    DevicePermissionError: [
        r'\baccess.*?not allowed\b',
        r'\baccess.*?denied\b',
    ],
    DeviceOperationAbortedError: [
        r'\boperation.*?cancell?ed\b',
        r'\bcancell?ed\s+by.*?user\b',
    ],
    DeviceNotFoundError: [
        r'\bno\s+devices\s+were\s+found\b',
    ],
    DevicePropertyExistsError: [
        r'\balready\s+enabled\b',
        r'\balready\s+disabled\b',
        r'50' # 50
    ],
}

def check_error(
    output: str,
    rc: Optional[int] = None,
    *,
    errors: Optional[Union[list[type[Exception]], type[Exception]]] = None
) -> None:
    if errors is None:
        errors = list(ERROR_MAP.keys())
    elif isinstance(errors, type):
        errors = [errors]
    
    for error, patterns in ERROR_MAP.items():
        if not error in errors:
            continue
            
        for regex in patterns:
            if re.search(regex, output, re.IGNORECASE) or re.search(regex, str(rc)): # In our case, an error code
                raise error(f"Output matches pattern '{regex}'\nOutput: {output}")
