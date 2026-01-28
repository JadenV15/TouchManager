
from .run import Run

#rc, out, err = Run.run_ps(r"pnputil /disable-device 'HID\ELAN2514&Col01\5&3a1afda2&0&0000'")
#rc, out, err = Run.run_ps('hello there; echo 123')
rc, out, err = Run.run_ps("echo 'access is denied'; exit 111", elevate=False, auto_elevate=True, propagate=True)

print(f"out: {out}, {type(out)}\nerr: {err}, {type(err)}\nrc: {rc}, {type(rc)}")
print(f"Powershell status: {Run.test_ps()}")