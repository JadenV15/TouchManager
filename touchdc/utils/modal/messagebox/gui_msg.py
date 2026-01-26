"""tkinter.messagebox constants and dialogs"""
__all__ = [
    "showinfo", "showwarning", "showerror",
    "askquestion", "askokcancel", "askyesno",
    "askyesnocancel", "askretrycancel",
    "ERROR", "INFO", "QUESTION", "WARNING",
    "ABORT", "RETRY", "IGNORE", "OK", "CANCEL", "YES", "NO",
    "ABORTRETRYIGNORE", "OKCANCEL", "RETRYCANCEL", "YESNO", "YESNOCANCEL"
]

from tkinter.messagebox import *

# icons
ERROR = "error"
INFO = "info"
QUESTION = "question"
WARNING = "warning"

# types
ABORTRETRYIGNORE = "abortretryignore"
OK = "ok"
OKCANCEL = "okcancel"
RETRYCANCEL = "retrycancel"
YESNO = "yesno"
YESNOCANCEL = "yesnocancel"

# replies
ABORT = "abort"
RETRY = "retry"
IGNORE = "ignore"
OK = "ok"
CANCEL = "cancel"
YES = "yes"
NO = "no"

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
    