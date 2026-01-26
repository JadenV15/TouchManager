"""Exceptions used by reg and run"""

from touchdc.errors import AppError # Base Error

# Generic Command error
class CommandError(AppError): pass

# Not enough permissions
class AccessDeniedError(CommandError): pass

# User cancelled the operation
class UserAbortedError(CommandError): pass

# Command not found, eg. `powershell -command hello`
class CommandNotFoundError(CommandError): pass

# PS disabled by admins/GP
class PowershellDisabledError(CommandError): pass


# Below: util for determining which exception to raise

# Note: There is no single way to know whether a command has succeeded or not. Sometimes it succeeds but the returncode is not 0. Sometimes it fails but the error goes to stdout instead of stderr. Or vice versa.

import re
from typing import Union, Optional

# These errors should hopefully be mutually exclusive
ERROR_MAP = {
    AccessDeniedError: [
        r'\baccess.*?not\s+allowed\b',
        r'\baccess.*?denied\b',
        r'PermissionDenied(?:Exception)?',
        r'SecurityException'
    ],
    UserAbortedError: [ # example: 'This command cannot be run due to the error: The operation was canceled by the user.'
        r'\boperation.*?cancell?ed\b',
        r'\bcancell?ed\s+by.*?user\b'
    ],
    CommandNotFoundError: [ # example: 'The term \'hello\' is not recognized as the name of a cmdlet, function, script file, or operable program.'
        r'\bthe\s+term.*?is\s+not\s+recogni[sz]ed\b',
        r'\bnot\s+recogni[sz]ed\s+as\s+the\s+name\s+of\b',
        r'CommandNotFound(?:Exception)?'
    ],
    PowershellDisabledError: [ # example: 'This program is blocked by group policy. For more information, contact your system administrator.'
        r'\b(?:program.*?blocked)?.*?group\s+policy\b',
        r'\b(?:contact\s+your\s+)?system\s+admins?(?:istrators?)?\b'
    ]
}

# In case anyone is wondering: https://stackoverflow.com/questions/72063066/python-3-typing-list-of-classes
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

