"""Run powershell commands with/without elevation"""

# TODO: add Locale support. there's a locale.ps1 file, but yet to be implemented.

from abc import ABC, abstractmethod
from typing import Union, Optional
import subprocess
import platform
import tempfile
import os

from touchdc.utils.modal import Ask
from .cmd_errors import *

class Run:
    """Utility to execute commands"""
    
    @classmethod
    def safe_path(cls, path):
        """Escape single quotes in a path so that it can be used in powershell single quote literal"""
        return path.replace("'", "''")
    
    @classmethod
    def run_ps(cls, cmd, *, elevate=False, auto_elevate=True, propogate=True, check=False) -> tuple[int, str, str]:
        """Run a powershell command.
        Args:
            cmd: the command to run, as a string. If this is an empty string, a newline may be used instead
            elevate: whether to prompt for elevation before running the command.
            auto_elevate: whether to detect permission failures and rerun the command with elevation if needed
            check: whether to raise appropriate errors from the errors.py file based on text output. When check is False, everything is left to the caller; only a few fatal exceptions will be raised (see below)
            propogate: whether to propogate the errorcode from the command itself, or return return powershell's errorcode (see info file for more info)
        Returns:
            Tuple containing the returncode, stdout and stderr
        Raises:
            CommandError: a domain error (defined in error file) occurred, and no meaningful output was recorded; the result may be of interest to the caller (eg. User aborted)
            RuntimeError: fatal or unexpected internal error
        """
        # See the info file for more info
        
        # Start hidden
        sinfo = None
        if platform.system().lower() == 'windows':
            sinfo = subprocess.STARTUPINFO()
            sinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        files = None
        
        try:
            if elevate:
                with (
                    tempfile.NamedTemporaryFile(mode='wb', suffix='.ps1', delete=False) as script_tmp,
                    tempfile.NamedTemporaryFile(mode='wb', delete=False) as stdout_tmp,
                    tempfile.NamedTemporaryFile(mode='wb', delete=False) as stderr_tmp,
                    tempfile.NamedTemporaryFile(mode='wb', delete=False) as retcode_tmp
                ):
                    
                    #leads to wrong behaviour. don't add a BOM yourself
                    #for f in (script_tmp, script_tmp, stderr_tmp, stderr_tmp): f.write(b'\xff\xfe')
                    
                    script_tmp.write(cmd.encode('utf-16-le')) #-le: no BOM
                    
                    script_file, stdout_file, stderr_file, retcode_file = script_tmp.name, stdout_tmp.name, stderr_tmp.name, retcode_tmp.name
                
                files = [script_file, stdout_file, stderr_file, retcode_file]
                
                ps_cmd = [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    ''.join([
                        # UTF-16-LE used as default for historical consistency (Get-/Set-Content often default to ANSI, for example) (note: PowerShell 5.1 does not have the 'utf8NoBOM' option for encoding)
                        # Error action is set to 'Stop' instead of 'Continue' so that no errors are ignored (eg. User cancelled elevation)
                        "try { $ErrorView = 'ConciseView'; $ErrorActionPreference = 'Stop'; $PSDefaultParameterValues['*:ErrorAction'] = 'Stop'; $PSDefaultParameterValues['*:Encoding'] = 'unicode'; $PSDefaultParameterValues['Disabled'] = $false } catch {}; ",
                        
                        f"$script = '{cls.safe_path(script_file)}'; ",
                        "$content = Get-Content -Raw -LiteralPath $script; ",
                        "$content = 'try { $PSDefaultParameterValues[''*:Encoding''] = ''unicode''; $PSDefaultParameterValues[''Disabled''] = $false } catch {}' + \"`n\" + $content + \"`n\"; ",
                        "Set-Content -LiteralPath $script -Value $content -Force | Out-Null; ",
                        
                        f"$stdout = '{cls.safe_path(stdout_file)}'; ",
                        f"$stderr = '{cls.safe_path(stderr_file)}'; ",
                        f"$retcode = '{cls.safe_path(retcode_file)}'; ",
                        
                        (
                            "$arg = @('-NoProfile','-ExecutionPolicy','Bypass','-Command',\"try { &$script 6>&1 5>&1 4>&1 3>&1 >$stdout 2>$stderr; `$exitcode = `$lastexitcode; if (`$exitcode) { exit `$exitcode } else { exit 0 } } catch { (`$_ | Out-String) >>$stderr; exit 1 }\"); "
                            if propogate
                            else
                            "$arg = @('-NoProfile','-ExecutionPolicy','Bypass','-Command',\"try { &$script 6>&1 5>&1 4>&1 3>&1 >$stdout 2>$stderr } catch { (`$_ | Out-String) >>$stderr; exit 1 }\"); "
                        ),
                        
                        "$p = Start-Process powershell -PassThru -Wait -Verb RunAs -WindowStyle Hidden -ArgumentList $arg; ",
                        "$p.ExitCode >$retcode; ",
                        
                        # Out-File has an option -NoNewline, but `>`/`>>` don't. This function both removes the added newline from a redirection file, and converts the file to BOMless utf-8.
                        "function Convert-Utf8NoBom { param([Parameter(Mandatory, ValueFromPipeline)][string]$Path) process { $content = Get-Content -Raw -LiteralPath $Path; if ($content -eq $null) { $content = '' }; $content = $content -Replace \"(\\r?\\n)$\", \"\"; New-Item -Path $Path -Force -Value $content; $Path } }; ",
                        
                        "foreach ($path in @($stdout, $stderr, $retcode)) { $path | Convert-Utf8NoBom | Out-Null }"
                    ])
                ]

                res = subprocess.run(
                    ps_cmd,
                    startupinfo=sinfo,
                    capture_output=True,
                    text=True
                )
                
                resout = res.stdout.strip()
                reserr = res.stderr.strip()
                resrc = res.returncode
                
                if resout or reserr: # The code should produce no output. Thus if there is output it must be unexpected error, and we cannot continue stably
                    check_error(resout+'\n'+reserr, resrc) # Check all errors. (Most likely a user cancelled error)
                    # If could not identify, raise runtimeerror
                    raise RuntimeError(f"Recieved unexpected output. Process stdout: \"{res.stdout}\" stderr: \"{res.stderr}\"")
                
                with (
                    open(stdout_file, encoding='utf-8') as _out,
                    open(stderr_file, encoding='utf-8') as _err,
                    open(retcode_file, encoding='utf-8') as _rc
                ):
                    out = _out.read() # .strip() not used because newline might be part of actual output
                    err = _err.read()
                    rc = _rc.read().strip() # open().read() returns a string, need to convert to int later
                    
                try:
                    rc = int(rc)
                except ValueError as e:
                    raise RuntimeError(f"Elevated command returned non-integer exit code '{rc}' of type '{type(rc).__name__}'") from e
                    
            else:
                ps_cmd = [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    (
                        cmd or r'"`n"' # Empty string causes "Cannot process the command because of a missing parameter. A command must follow -Command."
                        if propogate
                        else
                        (
                            "powershell -NoProfile -Command "
                            + (
                                ("'" + cls.safe_path(cmd) + "'")
                                if cmd
                                else r'"`n"'
                            )
                        )
                    ),
                ]
                
                res = subprocess.run(
                    ps_cmd,
                    startupinfo=sinfo,
                    capture_output=True,
                    text=True
                )
                
                out = res.stdout
                err = res.stderr
                rc = res.returncode # already int
                
            try:
                check_error(out+'\n'+err, rc, errors=AccessDeniedError)
            except AccessDeniedError as e:
                if auto_elevate and not elevate:
                    if Ask.elevate():
                        return cls.run_ps(cmd, elevate=True)
                    else:
                        raise UserAbortedError("Elevation cancelled by user") from e
                else: # nonfatal error
                    if check:
                        raise
            except CommandError:
                if check:
                    raise
                
            return rc, out, err
            
        finally:
            if 'files' in locals() and files is not None:
                for f in files:
                    if f and os.path.exists(f):
                        try:
                            os.remove(f)
                        except FileNotFoundError:
                            pass
                        except Exception as e:
                            print(f"Failed to cleanup file '{f}' after running elevated powershell: {e}")
    
    @classmethod    
    def test_ps(cls) -> bool:
        """Small wrapper to test whether powershell is enabled. In some corporate settings, powershell is disabled for non-admins
        Returns:
            bool
        """
        try:
            cls.run_ps('echo hello', elevate=False, auto_elevate=False)
        except PowershellDisabledError:
            return False
        else:
            return True
                            
 
if __name__ == '__main__':
    pass