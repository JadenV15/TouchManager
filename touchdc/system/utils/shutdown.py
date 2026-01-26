"""Small helper for triggering power options on Windows"""
__all__ = ['shutdown', 'restart', 'logoff']

from touchdc.system.command import Run

def shutdown():
    Run.run_ps('shutdown /s /f /t 0')
    
def restart():
    Run.run_ps('shutdown /r /f /t 0')
    
def logoff():
    Run.run_ps('shutdown /l /f')