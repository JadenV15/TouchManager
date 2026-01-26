"""A mirror of the tkinter.messagebox source for text dialogs"""
__all__ = [
    "showinfo", "showwarning", "showerror",
    "askquestion", "askokcancel", "askyesno",
    "askyesnocancel", "askretrycancel",
    "ERROR", "INFO", "QUESTION", "WARNING",
    "ABORT", "RETRY", "IGNORE", "OK", "CANCEL", "YES", "NO",
    "ABORTRETRYIGNORE", "OKCANCEL", "RETRYCANCEL", "YESNO", "YESNOCANCEL"
]

# Modified from source: https://github.com/python/cpython/blob/main/Lib/tkinter/messagebox.py

# Strangely (or perhaps it was intended), you can override any of the options in all functions. so `askyesno` could be configured to have type=YESNOCANCEL.

# icons
ERROR = "error"
INFO = "info"
QUESTION = "question"
WARNING = "warning"

# replies
ABORT = "abort"
RETRY = "retry"
IGNORE = "ignore"
OK = "ok"
CANCEL = "cancel"
YES = "yes"
NO = "no"

# types
ABORTRETRYIGNORE = (ABORT, RETRY, IGNORE)
OK
OKCANCEL = (OK, CANCEL)
RETRYCANCEL = (RETRY, CANCEL)
YESNO = (YES, NO)
YESNOCANCEL = (YES, NO, CANCEL)


def show(**kw):
    title = kw.get('title') or ''
    message = kw.get('message') or ''
    detail = kw.get('detail') or ''
    
    _type = kw.get('type') # Button set
    if not _type: # Buttons must be defined
        raise ValueError("Argument 'type' not specified")
    msg_type = kw.get('icon') # use the icon to get message type (warning, error, etc)
    if not msg_type: # Msg type must be defined
        raise ValueError("Argument 'icon' not specified")
    choices = _type if isinstance(_type, tuple) else (_type,) # OK -> (OK,)
    
    default = kw.get('default') # Default button
    if not default or default not in choices:
        default = choices[0]
    
    print(
        f"[{msg_type.capitalize()}]" # eg. [Error]
        + (f" {title}: " if title and title.lower() != msg_type.lower() else ' ') # to avoid repeating things like [Error] Error:
        + message
        + ('\n'+detail if detail else '')
    )
    
    if len(choices) == 1:
        pass # could have returned here, but the original is supposed to return OK when finished reading it. so wait for user input.
    
    while True:
        res = input(
            (' | '.join([f"[{c[0]}]{c[1:]}" for c in choices]))
            + (f" (Default: {default})" if len(choices) > 1 else ' (default)')
            + '> '
        )
        print()
        if not res:
            return default
        r = res.strip().lower()
        for c in choices:
            if r in (c.lower(), c[0].lower()):
                return c
        print('Please enter a valid option.\n')
        continue
        
    

def _show(title=None, message=None, _icon=None, _type=None, **options):
    if _icon and 'icon' not in options:
        options['icon'] = _icon
    if _type and 'type' not in options:
        options['type'] = _type
    if title is not None:
        options['title'] = title
    if message is not None:
        options['message'] = message
    
    return show(**options)
            

# 'show info' type dialogs - return button name (OK)

def showinfo(title=None, message=None, **options):
    "Show an info message"
    return _show(title, message, INFO, OK, **options)# == OK   - tkinter just returns the clicked button name


def showwarning(title=None, message=None, **options):
    "Show a warning message"
    return _show(title, message, WARNING, OK, **options)


def showerror(title=None, message=None, **options):
    "Show an error message"
    return _show(title, message, ERROR, OK, **options)

# 'ask' type dialogs

# return button name:
def askquestion(title=None, message=None, **options):
    "Ask a question"
    return _show(title, message, QUESTION, YESNO, **options)

# return True/False/None:

def askokcancel(title=None, message=None, **options):
    "Ask if operation should proceed; return true if the answer is ok"
    s = _show(title, message, QUESTION, OKCANCEL, **options)
    return s == OK


def askyesno(title=None, message=None, **options):
    "Ask a question; return true if the answer is yes"
    s = _show(title, message, QUESTION, YESNO, **options)
    return s == YES


def askyesnocancel(title=None, message=None, **options):
    "Ask a question; return true if the answer is yes, false if no, None if cancelled."
    s = _show(title, message, QUESTION, YESNOCANCEL, **options)
    if s == CANCEL:
        return None
    return s == YES


def askretrycancel(title=None, message=None, **options):
    "Ask if operation should be retried; return true if the answer is yes"
    s = _show(title, message, WARNING, RETRYCANCEL, **options)
    return s == RETRY

# Tests
if __name__ == "__main__":

    print("info", showinfo("Spam", "Egg Information"))
    print("warning", showwarning("Spam", "Egg Warning"))
    print("error", showerror("Spam", "Egg Alert"))
    print("question", askquestion("Spam", "Question?"))
    print("proceed", askokcancel("Spam", "Proceed?"))
    print("yes/no", askyesno("Spam", "Got it?"))
    print("yes/no/cancel", askyesnocancel("Spam", "Want it?"))
    print("try again", askretrycancel("Spam", "Try again?"))
    