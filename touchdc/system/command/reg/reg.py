"""Run registry commands - add, remove, test registry paths, keys, values"""

# TODO: migrate to winreg
# todo - test more uncommon reg types

import os
import json
import tempfile
from typing import Optional, Union, Any
from functools import wraps

from touchdc.utils.modal import Ask
from touchdc.system.command.run import Run, cmd_errors # try to prevent circular import by using command.run instead of command
from .reg_errors import *

class Reg:
    """Utility to read and write from the registry with powershell"""
    
    # References: https://learn.microsoft.com/en-us/windows/win32/sysinfo/registry-value-types, https://learn.microsoft.com/en-us/troubleshoot/windows-server/performance/windows-registry-advanced-users
    
    # Winnt.h Enum (https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_registry_provider?view=powershell-7.5#type-microsoftwin32registryvaluekind)
    WINAPI_REG_TYPES = {
        "REG_NONE": 0,
        "REG_SZ": 1,
        "REG_EXPAND_SZ": 2,
        "REG_BINARY": 3,
        "REG_DWORD": 4,
        "REG_DWORD_LITTLE_ENDIAN": 4,   # alias
        "REG_DWORD_BIG_ENDIAN": 5,
        "REG_LINK": 6,
        "REG_MULTI_SZ": 7,
        "REG_RESOURCE_LIST": 8,
        "REG_FULL_RESOURCE_DESCRIPTOR": 9,
        "REG_RESOURCE_REQUIREMENTS_LIST": 10,
        "REG_QWORD": 11,
        "REG_QWORD_LITTLE_ENDIAN": 11,  # alias
    }
    # RegistryValueKind (.GetValueKind()) Enum (https://learn.microsoft.com/en-us/dotnet/api/microsoft.win32.registryvaluekind?view=net-10.0)
    REG_VALUE_KINDS = {
        "NONE": -1,
        "UNKNOWN": 0,
        "STRING": 1,
        "EXPANDSTRING": 2,
        "BINARY": 3,
        "DWORD": 4,
        "MULTISTRING": 7,
        "QWORD": 11,
    }
    REG_VALUE_KIND_NAMES = {
        -1: "NONE",
        0: "UNKNOWN",
        1: "STRING",
        2: "EXPANDSTRING",
        3: "BINARY",
        4: "DWORD",
        7: "MULTISTRING",
        11: "QWORD",
    }
    REG_FRIENDLY_NAMES = {
        "NONE": "None",
        "UNKNOWN": "Unknown",
        "STRING": "String",
        "EXPANDSTRING": "ExpandString",
        "BINARY": "Binary",
        "DWORD": "DWord",
        "MULTISTRING": "MultiString",
        "QWORD": "QWord",
    }
    # RegistryValueKind supported types
    SUPPORTED_REG_TYPES = {-1, 0, 1, 2, 3, 4, 7, 11}
    
    @classmethod
    def normalise(cls, *types: Union[int, str]) -> Union[int, list[int]]:
        """Normalise inconsistent registry type output to an integer
        Args:
            types: a reg type(s) (eg. 1, 'REG_DWORD', 'DWORD', 'DWord') passed positionally
        Returns:
            The normalised type if one was passed, else a list of them.
        Raises:
            TypeError: if the argument type was incorrect
            ValueError: if a normalised reg type could not be found based on the value of the argument
        """
        norm_types = []
        
        for t in types:
            if isinstance(t, int):
                i = t
                
            elif isinstance(t, str):
                t = t.strip().upper()
                
                if t.startswith('REG_'):
                    i = cls.WINAPI_REG_TYPES.get(t)
                    if i is None:
                        raise ValueError(f"Could not find reg type: '{t}'")
                    
                else:
                    i = cls.WINAPI_REG_TYPES.get('REG_'+t)
                    if i is None:
                        i = cls.REG_VALUE_KINDS.get(t)
                        if i is None:
                            raise ValueError(f"Could not find reg type: '{t}'")
                
            else:
                raise TypeError(f"Wrong type '{type(t).__name__}': '{t}'")
            
            if not i in cls.SUPPORTED_REG_TYPES:
                i = 0
            norm_types.append(i)
                
        if len(norm_types) == 1:
            return norm_types[0]
            
        return norm_types
    
    @classmethod
    def get_name(cls, *types: Union[int, str], pretty=False) -> Union[int, list[int]]:
        """Get the name of a registry type of any format
        Args:
            types: a reg type(s) (eg. 1, 'REG_DWORD', 'DWORD', 'DWord') passed positionally
            pretty: whether to use a stylised string. Eg. 'DWord' instead of 'DWORD' (all caps)
        Returns:
            The name if one type was passed, else a list of names.
        Raises:
            See errors of normalise()
            ValueError: if a normalised name could not be found based on the value of the argument
        """
        name_types = []
        
        for t in types:
            i = cls.normalise(t)
            if not isinstance(i, int):
                raise ValueError(f"Could not normalise to int: '{i}'")
            
            t = cls.REG_VALUE_KIND_NAMES.get(i)
            if t is None:
                raise ValueError(f"Could not find the name for reg type: '{i}'")
                
            if pretty:
                t = cls.REG_FRIENDLY_NAMES.get(t)
                if t is None:
                    raise ValueError(f"Could not find the friendly name for reg type: '{i}'")
                
            name_types.append(t)
        
        if len(name_types) == 1:
            return name_types[0]
        
        return name_types
    
    @staticmethod
    def handle_error(func):
        """Handles errors that may occur
        Takes errors generated by Run and wraps them as Reg errors, to be propogated to the controller
        """
        @wraps(func)
        def magic(*args, **kw):
            try:
                return func(*args, **kw)
            except cmd_errors.UserAbortedError as e:
                raise RegistryOperationAbortedError(f"Registry operation was aborted by the user") from e
            except cmd_errors.AccessDeniedError as e:
                raise RegistryPermissionError(f"Not enough permissions to complete the registry operation") from e
        return magic
    
    @classmethod
    @handle_error
    def test_reg(cls, path, name=None, elevate=False, auto_elevate=True) -> bool:
        """Test whether a reg path (and optionally a reg value) exists
        Args (Common args):
            path: path of the reg key (example: r"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer")
            name: optional name of the reg value. If this is specified then both `path` and `name` must exist for the method to return True.
            elevate: whether to request elevation
            auto_elevate: whether to detect permission failures and rerun the method with elevation
        Returns:
            bool
        Raises:
            RuntimeError: fatal or unexpected internal error
        """
        if name is None:
            rc, out, err = Run.run_ps(f"Test-Path -LiteralPath '{Run.safe_path(path)}'", elevate=elevate, auto_elevate=auto_elevate)
            if out.strip().lower() == 'true':
                return True
            elif out.strip().lower() == 'false':
                return False
            else:
                raise RuntimeError(f"Test-Path failed with stdout: '{out}'\nstderr: '{err}'")
                
        else:
            try:
                reg_data, reg_type = cls.get_reg(path, name, elevate=elevate, auto_elevate=auto_elevate)
            except RegistryItemNotFoundError:
                return False
            else:
                return True
    
    @classmethod
    @handle_error
    def get_reg(cls, path, name, elevate=False, auto_elevate=True) -> tuple[Any, int]:
        """Get a reg value
        Args:
            See common args
        Returns:
            Tuple of the data and reg type of the value
        Raises:
            RegistryError (commonly RegistryItemNotFoundError if the path or name is not found): a registry-related domain error as defined in the error file
            RuntimeError: fatal or unexpected internal error
        """
        
        r'''Powershell examples:
PS C:\> $key = Get-Item -literalpath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer'
PS C:\> $key.GetValue('hello')
PS C:\> $key.GetValueKind('hello')
Exception calling "GetValueKind" with "1" argument(s): "The specified registry key does not exist."
At line:1 char:1
+ $key.GetValueKind('hello')
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (:) [], MethodInvocationException
    + FullyQualifiedErrorId : IOException

PS C:\> # Only GetValueKind raises an error.
PS C:\> # GetValue has an optional parameter to return if fail, default $null.
PS C:\> $key.GetValue('hello', 123)
123
PS C:\> #GetValueKind doesn't.
PS C:\> $key.GetValueKind('hello', 123)
Cannot find an overload for "GetValueKind" and the argument count: "2".
At line:1 char:1
+ $key.GetValueKind('hello', 123)
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (:) [], MethodException
    + FullyQualifiedErrorId : MethodCountCouldNotFindBest
PS C:\> $key.GetValue('hello') -eq ($null)
True
PS C:\> $key.GetValue('hello') -eq ('')
False
        '''
        try:
            json_file = None
            
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
                json_file = tmp.name
            
            rc, out, err = Run.run_ps(
                (
                    # this logic is used because we want the reg type as well.
                    f"$key = Get-Item -LiteralPath '{Run.safe_path(path)}'; "
                    
                    f"$data = $key.GetValue('{name}', $null); "
                    "if ($data -eq $null) { throw [System.Management.Automation.ItemNotFoundException] }; "
                    f"$type = $key.GetValueKind('{name}'); " # No fallback arg, unlike GetValue
                
                    "$table = @{data = $data; type = $type}; " # Type is a string here
                    "$json = $table | ConvertTo-Json -Compress; "
                    
                    f"$json_file = '{Run.safe_path(json_file)}'; "
                    "$json >$json_file; "
                    "New-Item -Path $json_file -Force -Value (Get-Content -Raw -LiteralPath $json_file) | Out-Null" # convert BOM-less utf8
                ),
                elevate=elevate,
                auto_elevate=auto_elevate
            )
            
            if out.strip() or err.strip(): # should be no output, if there is, then its an error
                try:
                    check_error(out+'\n'+err, rc)
                except RegistryPermissionError:
                    if auto_elevate and not elevate and Ask.elevate():
                        return cls.get_reg(path, name, elevate=True)
                    else:
                        raise
                else:
                    raise RuntimeError(f"Recieved unexpected output. Process stdout: \"{out}\" stderr: \"{err}\"")
            
            with open(json_file, encoding='utf-8') as f:
                output = f.read().strip()
            assert output
        
        finally:
            if 'json_file' in locals() and json_file is not None and os.path.exists(json_file):
                try:
                    os.remove(json_file)
                except FileNotFoundError:
                    pass
                except Exception as e:
                    print(f"Failed to cleanup file '{json_file}' after getting registry value: {e}")

        try:
            table = json.loads(output.strip())
            return table['data'], cls.normalise(table['type']) # Int
            # Important note: table['data'] could be any type, not just str (e.g. int for DWORDs)
        except json.JSONDecodeError as e:
            raise RuntimeError('Failed to get registry value from json') from e
    
    # TODO: add a toggle when multiple subkeys must be deleted/created via -Force
    
    @classmethod
    @handle_error
    def set_reg(cls, path, name=None, value=None, reg_type=None, skip=True, elevate=False, auto_elevate=True) -> None:
        """Set a reg key or value. Create all intermediate keys if needed.
        Args:
            See commmon args
            skip: whether to check if the value is already set correctly, and if so skip having to set it.
        Return:
            None
        Raises:
            ValueError: incorrect arguments
            RegistryError: a registry-related domain error as defined in the error file
            RuntimeError: fatal & unexpected internal error
        """
        if all([v is not None for v in (name, value, reg_type)]):
            new_property = True # do we need to set a property, or do they just want the key
        elif all([v is None for v in (name, value, reg_type)]):
            new_property = False # just create the key
        else:
            raise ValueError("Bad parameter set")
        
        if skip:
            if new_property:
                try:
                    get_val, get_type = cls.get_reg(path, name, elevate=elevate, auto_elevate=auto_elevate)
                    if (get_val, cls.normalise(get_type)) == (value, cls.normalise(reg_type)):
                        return
                except RegistryItemNotFoundError:
                    pass
        
        if cls.test_reg(path, elevate=elevate, auto_elevate=auto_elevate):
            if not new_property:
                return # return, even if skip=False, because the path exists, what else is there to do?
            
            # Path already exists, use Set-ItemProperty
            rc, out, err = Run.run_ps(f"Set-ItemProperty -LiteralPath '{Run.safe_path(path)}' -Name '{name}' -Value '{value}' -Type '{cls.get_name(reg_type)}' -Force | Out-Null", elevate=elevate, auto_elevate=auto_elevate) # not using safe_path because these aren't file paths
                        
        else:
            # New-Item is for creating NEW items
            # With -Force: If an existing path is provided then it will be overwritten. If a path with nonexistent parent keys is provided, the keys will be created.
            # If not -Force, it will raise an error.
            
            # New-ItemProperty is for creating NEW properties, Set-ItemProperty can create or overwrite.
            # We are creating a new path & value anyway, so
            # use New-ItemProperty (-Type replaced with -PropertyType)
            
            if not cls.test_reg(path, elevate=elevate, auto_elevate=auto_elevate): # Ensure we don't overwrite an existing key
                raise RuntimeError("Detected an exisitng key. Raising to prevent overwriting")
            
            # New-Item has no -LiteralPath
            _, out, err = Run.run_ps(
                f"New-Item -Path '{Run.safe_path(path)}' -Force"
                + (
                    f" | New-ItemProperty -Name '{name}' -Value '{value}' -PropertyType '{cls.get_name(reg_type)}' -Force | Out-Null" 
                    if new_property
                    else ' | Out-Null'
                ),
                elevate=elevate,
                auto_elevate=auto_elevate
            )
            
        if out.strip() or err.strip(): # we expect no output, so if there is, it must be error.
            try:
                check_error(out+'\n'+err)
            except RegistryPermissionError:
                if auto_elevate and not elevate and Ask.elevate():
                    return cls.set_reg(path, name, elevate=True)
                else:
                    raise
            else:
                raise RuntimeError(f"Unexpected output. Process stdout: \"{out}\"\nstderr: \"{err}\"")
    
    @classmethod
    @handle_error
    def del_reg(cls, path, name=None, elevate=False, auto_elevate=True) -> None:
        """Delete a registry key or value forcefully and recursively
        Args:
            See common args
            name: optional name of the registry value. If specified, remove the value instead of the key in `path`.
        Return:
            None
        Raises:
            RegistryError: a registry-related domain error as defined in the error file
            RuntimeError: fatal & unexpected internal error
        """
        
        r'''Examples:
PS C:\Users\test> # I created the keys test1\test2
PS C:\Users\test> Remove-Item -LiteralPath HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\test1\test2
PS C:\Users\test> Remove-Item -LiteralPath HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\test1\test2 -Force
PS C:\Users\test> Remove-Item -LiteralPath HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\test1

Confirm
The item at HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\test1 has children and the Recurse
parameter was not specified. If you continue, all children will be removed with the item. Are you sure you want to
continue?
[Y] Yes  [A] Yes to All  [N] No  [L] No to All  [S] Suspend  [?] Help (default is "Y"): N
PS C:\Users\test> Remove-Item -LiteralPath HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\test1 -Force

Confirm
The item at HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\test1 has children and the Recurse
parameter was not specified. If you continue, all children will be removed with the item. Are you sure you want to
continue?
[Y] Yes  [A] Yes to All  [N] No  [L] No to All  [S] Suspend  [?] Help (default is "Y"): N
PS C:\Users\test> Remove-Item -LiteralPath HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\test1 -Recurse
PS C:\Users\test> Remove-Item -LiteralPath HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\test1 -Recurse -Force
PS C:\Users\test> 
        '''
        
        if not cls.test_reg(path, name=name, elevate=elevate, auto_elevate=auto_elevate):
            return # The path/value is already "deleted" if it can't be found
        
        rc, out, err = Run.run_ps(
            (
                f"Remove-Item -LiteralPath '{path}' -Recurse -Force | Out-Null" # remove entire key recursively
                if name is None and path
                else f"Remove-ItemProperty -LiteralPath '{path}' -Name '{name}' -Force | Out-Null" # remove value
            ),
            elevate=elevate,
            auto_elevate=auto_elevate
        )
            
        if out.strip() or err.strip(): # we expect no output (Out-Null), so if there is, it must be error.
            try:
                check_error(out+'\n'+err)
            except RegistryPermissionError:
                if auto_elevate and not elevate and Ask.elevate():
                    return cls.del_reg(path, name, elevate=True)
                else:
                    raise
            else:
                raise RuntimeError(f"Unexpected output. Process stdout: \"{out}\" stderr: \"{err}\"")
            
            
# Example key: HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer
if __name__ == '__main__':
    pass