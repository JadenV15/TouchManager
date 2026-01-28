# Running PowerShell from Python — Notes

(split into sections / summarised / formatted by chatgpt)

## TL;DR (Summary)

- Unelevated PowerShell commands can be run safely via `subprocess.run(["powershell", "-NoProfile", "-Command", cmd])`, but quoting and empty commands require care.
- PowerShell has **7 output streams**; streams 3–6 are collapsed into `stdout` unless redirected explicitly.
- Hiding the PowerShell window requires **Windows-only** `subprocess.STARTUPINFO`.
- Elevation requires `Start-Process -Verb RunAs`, which:
  - breaks `-RedirectStandardOutput/-RedirectStandardError` in Windows PowerShell 5.1
  - removes those flags entirely in PowerShell Core 7.x
- The only cross-version way to capture output from elevated commands:
  1. Redirect inside the elevated PowerShell process
  2. Write stdout/stderr to temp files
  3. Read them back from Python
- When running scripts (not inline commands), redirection must occur inside `-Command` using the **call operator** (`&`).
- PowerShell text encoding is inconsistent across versions:
  - Windows PowerShell defaults to **UTF-16-LE with BOM**
  - PowerShell Core defaults to **UTF-8 without BOM**
  
  Reliable cross-version conversion to UTF-8-no-BOM:

  `New-Item -Value (Get-Content -Raw ...)`

  This conversion requires the source file to have a BOM if it is UTF-16.

- `$LASTEXITCODE`:
  - is set only by native executables or `exit`
  - is not affected by most cmdlet errors
  - is global to the PowerShell process

- Most PowerShell errors are non-terminating and do not stop execution unless:
  - `$ErrorActionPreference = 'Stop'`
  - or `-ErrorAction Stop` is applied

- To reliably propagate failure:
  - force terminating errors
  - wrap execution in try/catch
  - explicitly `exit <code>` in catch

---

## 1. Running PowerShell via Python (subprocess)

PowerShell can be invoked from Python using `subprocess.run`:

`res = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True)`

- `res.returncode` → exit code  
- `res.stdout` → standard output  
- `res.stderr` → standard error  

> If `cmd` is an empty string, PowerShell treats `-Command` as missing and displays help instead.

---

## 2. PowerShell Output Streams

PowerShell defines **7 streams**:

| Stream | Purpose     | Write Cmdlet           |
|--------|------------|----------------------|
| 1      | Success     | Write-Output          |
| 2      | Error       | Write-Error           |
| 3      | Warning     | Write-Warning         |
| 4      | Verbose     | Write-Verbose         |
| 5      | Debug       | Write-Debug           |
| 6      | Information | Write-Information     |
| n/a    | Progress    | Write-Progress        |

> When invoked non-interactively, streams 3–6 are collapsed into `stdout`.

Example redirection pattern:  

`6>&1 5>&1 4>&1 3>&1 2>$stderr >$stdout`

---

## 3. Hiding the PowerShell Window (Windows Only)

To prevent the PowerShell console window from appearing:

```python
sinfo = None
if platform.system().lower() == 'windows':
    sinfo = subprocess.STARTUPINFO()
    sinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
```

---

## 4. Quoting Pitfalls with -Command

PowerShell parses quoting before executing the command.  

Incorrect example:

`subprocess.run(['powershell', '-Command', "'echo ''hi there''; exit 111'"])`  

> Fails because the outer PowerShell consumes the quotes.

Correct pattern:  

`powershell -Command "powershell -Command 'echo ''hi there''; exit 111'"`  

> Only the inner PowerShell receives the intended quoting.

---

## 5. Elevation via Start-Process -Verb RunAs

Elevation requires Start-Process:

`Start-Process powershell -Verb RunAs -Wait -WindowStyle Hidden`

To retrieve the exit code:

```powershell
$p = Start-Process -PassThru ...
$p.ExitCode
```

---

## 6. Why -RedirectStandardOutput Breaks with Elevation

- In Windows PowerShell 5.1, `Start-Process` has two parameter sets: **Default** and **UseShellExecute**  
  `-Verb` and `-RedirectStandard*` belong to different sets and cannot be combined.
- In PowerShell Core 7.x: `-RedirectStandard*` flags do not exist.

> You cannot rely on Start-Process redirection in a cross-version way when elevating.

---

## 7. Redirecting Output from Elevated Commands (Working Pattern)

Redirection must happen **inside the elevated PowerShell process**:

`Start-Process powershell -Wait -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-Command',"& $script > $stdout 2> $stderr")`

Key points:  
- Use `-Command`, not `-File`  
- Use the call operator `&`  
- Redirect inside the elevated process  
- Works for both commands and scripts

---

## 8. Temporary Files for Elevated Execution

Because output is redirected to files:

```python
with (tempfile.NamedTemporaryFile(mode='wb', suffix='.ps1', delete=False), tempfile.NamedTemporaryFile(mode='wb', delete=False), tempfile.NamedTemporaryFile(mode='wb', delete=False)):
    ...
```

> The script file is written as UTF-16-LE (without BOM initially).

---

## 9. PowerShell Encoding Inconsistencies

Encoding defaults differ:

| Environment         | Default                  |
|--------------------|--------------------------|
| Windows PowerShell  | UTF-16-LE with BOM       |
| PowerShell Core     | UTF-8 without BOM        |

Additional issues:  
- `Out-File` prepends a BOM  
- `Set-Content` defaults to ANSI  
- `>` and `>>` behave like `Out-File`  
- Python’s `open()` relies on BOM presence for UTF-16 detection

---

## 10. Converting Output to UTF-8-No-BOM (Cross-Version)

Reliable method:

`New-Item -Path $path -Force -Value (Get-Content -LiteralPath $path -Raw)`

Observations:  
- Works for UTF-16 only if a BOM is present  
- Fails for UTF-16 files without BOM  
- Successfully converts UTF-8 with or without BOM  

> Files redirected by PowerShell must include a BOM before conversion.

---

## 11. Exit Codes and $LASTEXITCODE

- `$LASTEXITCODE` is set only by native executables or `exit`  
- Cmdlet failures do not affect it  
- Global to the PowerShell process

`powershell -Command` returns:  
- `0` on success  
- `1` on terminating error  
- unless overridden by `exit <code>`

---

## 12. PowerShell Error Types

**Non-terminating errors**:  
- Default behavior: execution continues  
- Often redirectable (2>$null)  
- Example: `Write-Error`

**Terminating errors**:  
- Stop execution  
- Catchable with try/catch  
- Example: `throw`, division by zero (with `ErrorAction=Stop`)

---

## 13. Enforcing Reliable Failure Semantics

To prevent silent failure, set global error handling:

```powershell
$ErrorActionPreference = 'Stop'  
$PSDefaultParameterValues['*:ErrorAction'] = 'Stop'
```

Recommended execution pattern:

```powershell
try {
  & $script 6>&1 5>&1 4>&1 3>&1 >$stdout 2>$stderr
}
catch {
  ($_ | Out-String) >> $stderr
  exit 1
}
```

> This ensures:
> - All streams are captured
> - Terminating errors are logged
> - Exit code is meaningful

---

## 14. Script Exit Code Rules

A PowerShell script sets `$LASTEXITCODE` only if:  
- It runs a native executable and does not override the result  
- It explicitly calls `exit <code>`  

> Scripts do not inherit `$ErrorActionPreference` from the parent PowerShell process when invoked via `powershell -Command`.

## 15. Improvements

Improvements include:
- Add support for different locales/cultures (in progress)