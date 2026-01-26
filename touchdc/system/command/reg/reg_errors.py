"""Exceptions used by Reg"""

from touchdc.errors import AppError # Base Error

# Generic registry error
class RegistryError(AppError): pass

# Cancelled by user
class RegistryOperationAbortedError(RegistryError): pass

# Not enough permissions
class RegistryPermissionError(RegistryError): pass

# No such item/path
class RegistryItemNotFoundError(RegistryError): pass

# Item already exists
class RegistryItemExistsError(RegistryError): pass


import re
from typing import Union, Optional

ERROR_MAP = {
    RegistryPermissionError: [
        r'\baccess.*?not\s+allowed\b',
        r'\baccess.*?denied\b',
        r'PermissionDenied(?:Exception)?',
        r'SecurityException'
    ],
    RegistryItemNotFoundError: [
        r'\bcannot\s+find\s+path\b',
        r'\bdoes\s+not\s+exist\b', # eg. The specified registry key does not exist.
        #r'ObjectNotFound', - too general
        r'PathNotFound(?:Exception)?',
        r'ItemNotFound(?:Exception)?'
    ],
    RegistryItemExistsError: [
        r'\balready\s+exists\b',
        r'ResourceExists(?:Exception)?'
    ]
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
            if re.search(regex, output, re.IGNORECASE):
                raise error(f"Output matches pattern '{regex}'\nOutput: {output}")

