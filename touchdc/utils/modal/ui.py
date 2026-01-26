"""Create user dialogs"""
__all__ = ['Info', 'Error', 'Ask']

import sys
import tkinter as tk
from tkinter import ttk

from touchdc.ui.utils.dpi import scale
from . import setting

if setting.mode == 'gui':
    from .messagebox import gui_msg as msg
    from .custom import gui_msg as custom
else:
    from .messagebox import cli_msg as msg
    from .custom import cli_msg as custom

"""the zen: flat is better than nested"""

class Info:
    """Info dialogs. Click OK"""
    
    @classmethod
    def showinfo(cls, message, **kw):
        args = {
            'title': 'Info',
            'message': message,
            **kw
        }
        
        return msg.showinfo(**args) == msg.OK
        
    @classmethod
    def warn(cls, message, **kw):
        args = {
            'title': 'Warning',
            'message': message,
            **kw
        }
        
        return msg.showwarning(**args) == msg.OK

class Error:
    """Error dialogs. Click OK"""
    
    @classmethod
    def unexpected(cls, **kw):
        args = {
            'parent': tk._default_root or None,
            'title': 'Error',
            'message': 'An unexpected error occurred. Please try again later.',
            'detail': None,
            **kw
        }
        
        return msg.showerror(**args) == msg.OK

    @classmethod
    def access_denied(cls, **kw):
        args = {
            'parent': tk._default_root or None,
            'title': 'Error',
            'message': 'Not enough permissions to complete the operation',
            'detail': None,
            **kw
        }
        
        return msg.showerror(**args) == msg.OK
        
    @classmethod
    def aborted(cls, **kw):
        args = {
            'parent': tk._default_root or None,
            'title': 'Error',
            'message': 'The operation was cancelled by the user.',
            'detail': None,
            **kw
        }
        
        return msg.showerror(**args) == msg.OK

    
class Ask:
    """Ask a question. Return True/False/None"""
    
    @classmethod
    def yesno(cls, **kw):
        args = {
            'parent': tk._default_root or None,
            'title': 'Question',
            'detail': None,
            **kw
        }
        
        return msg.askyesno(**args)
    
    @classmethod
    def warnyesno(cls, message, **kw):
        args = {
            'parent': tk._default_root or None,
            'title': 'Warning',
            'message': message,
            'type': msg.YESNO,
            'default': msg.YES,
            'icon': msg.WARNING,
            **kw
        }
        
        return msg.askyesno(**args)
    
    @classmethod
    def elevate(cls, **kw):
        args = {
            'parent': tk._default_root or None,
            'title': 'Question',
            'message': """To complete the operation, your consent is required.
Clicking 'yes' will open a dialogue asking for your permission. Clicking 'no' will cancel the operation without making any changes.
Do you wish to proceed?""",
            'detail': None,
            **kw
        }
        
        return msg.askyesno(**args)
    
    @classmethod
    def option(cls, options, **kw):
        args = {
            'parent': tk._default_root or None,
            'title': 'Option',
            'message': 'Please choose one of the following options: ',
            'options': options,
            'default': None,
            **kw
        }
        
        return custom.option(**args)
        
    @classmethod
    def button_option(cls, options, **kw):
        args = {
            'parent': tk._default_root or None,
            'title': 'Option',
            'message': 'Please choose an action',
            'options': options,
            'default': None,
            **kw
        }
        
        return custom.button_option(**args)


if __name__ == '__main__':
    print(Info.showinfo(message='hi there'))
    
    print(Error.unexpected())

    print(Error.access_denied())
    
    print(Error.aborted())
    
    print(Ask.elevate())
    
    print(Ask.warnyesno(message='You are about to blow up the town!'))
    
    print(Ask.option(
        title="Dinner",
        message="Choose your meal:",
        options=[
            (
                "Large Italian pizza",
                "code_name_pizza",
                "Mushrooms, cheese, truffle oil, tomato sauce, basil leaves"
            ),
            (
                "Bowl of pasta",
                "code_name_pasta",
                "Cheese, basil, tomato sauce"
            ),
        ],
        default="code_name_pasta"
    ))
    
    print(Ask.button_option(
        title="Action",
        message="Save yourself or the whole world?",
        options=[
            ("Me", "yourself"),
            ("The World", "world")
        ]
    ))
    