import sys
from .reg import Reg

base = r"HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" # base test key

def test_existing():
    assert Reg.test_reg(base, 'NoDriveTypeAutoRun')
def test_none():
    assert not Reg.test_reg(base+r'\IMAGINARY123')
def get_existing():
    return Reg.get_reg(base, 'NoDriveTypeAutoRun')
def get_none():
    try:
        Reg.get_reg(base, 'IMAGINARY123')
    except Exception:
        return
    else:
        assert False
def set_key():
    return Reg.set_reg(base+r'\test1\test2')
def set_existing_key(): #caution
    return Reg.set_reg(base)
def set_val(): # Note: strangely, requires elevation to add a value
    return Reg.set_reg(base, 'testval', 1, 'DWord')
def del_val():
    set_val()
    return Reg.del_reg(base, 'testval')
def del_key():
    set_key()
    return Reg.del_reg(base+r'\test1')
    
if __name__ == '__main__':
    assert Reg.test_reg(base)
    
    #test
    #data, type_ = Reg.get_reg(base, 'NoDriveTypeAutoRun')
    #print(data, type(data))
    #print(type_, type(type_))
    ##both ints, as expected
    
    for f in (
        test_existing,
        test_none,
        get_existing,
        get_none,
        set_key,
        set_existing_key,
        set_val,
        del_val,
        del_key
    ):
        input('> ')
        print(f"Testing: {f.__name__}")
        try:
            result = f()
            print(f"- Result Success: {result}")
        except Exception as e:
            print(f"- Failed: {e}")