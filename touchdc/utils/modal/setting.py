"""Experimental GUI/CLI setting toggle"""

mode = 'gui'

def set_mode(new_mode):
    global mode
    assert new_mode in ('gui', 'cli')
    mode = new_mode