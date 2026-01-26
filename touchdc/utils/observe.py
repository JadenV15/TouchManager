"""Observer pattern, modified from original source found at https://github.com/ajongbloets/julesTk
Always detach expired listeners to avoid problems (https://en.wikipedia.org/wiki/Lapsed_listener_problem)
"""

# MIT License
#
# Copyright (c) 2017 Joeri Jongbloets
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__author__ = "Joeri Jongbloets <joeri@jongbloets.net>"
__all__ = ['Observable', 'Observer']

from functools import wraps
from abc import ABC, abstractmethod

# the ultimate guide: how to waste your time
import subprocess
import sys
import platform
try:
    from weakref import WeakSet
except ImportError:
    try:
        from weakrefset import WeakSet
    except ImportError:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'): # for pyinstaller, where sys.executable is this
            raise RuntimeError("Could not install package weakrefset: script frozen.")
        else:
            try:
                sinfo = None
                if platform.system().lower() == 'windows':
                    sinfo = subprocess.STARTUPINFO()
                    sinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'weakrefset'])
                from weakrefset import WeakSet
            except (subprocess.CalledProcessError, ImportError) as e:
                raise RuntimeError("Could not install package weakrefset: {e}.")


class Observable:
    """An Observable will update its observers whenever it is changed

    Notification can be triggered in two ways:

    1. Call `notify()` directly from a method, after data was updated
    2. Use `@observed` decorator for methods that should call `notify` when finished

    Observers can register themselves using the `attach` method.
    Only 1 observer registration per object.

    """

    def __init__(self):
        #self._observers = []
        self._observers = WeakSet()

    def attach(self, observer):
        """Register an observer to get notified when this object is changed.

        Will only add the observer if it is not already observing.

        :param observer: The observer that should be notified
        :type observer: Observer
        """
        if not isinstance(observer, Observer):
            raise ValueError("Expected a Observer, not {}".format(type(observer)))
        self._observers.add(observer)
    
    def detach(self, observer):
        """Remove an observer

        Will only remove the observer if it is already observing.

        :param observer: The observer that should be removed
        :type observer: Observer
        """
        
        if not isinstance(observer, Observer):
            raise ValueError("Expected a Observer, not {}".format(type(observer)))
        self._observers.discard(observer)
    
    def notify(self):
        """Notifies all observing observers"""
        for observer in self._observers:
            try:
                observer.update(self)
            except Exception as e:
                raise#print(f"Failed to update observer {observer}: {e}") - better to fail fast then go unnoticed
    
    @staticmethod
    def observed(f):
        """Decorator that will automatically call notify_observers after executing this method
        Caller must inherit this class
        
        :type f: callable
        """
        @wraps(f)
        def magic(self, *args, **kwargs):
            try:
                result = f(self, *args, **kwargs)
            except Exception:
                raise
            else:
                self.notify()
                return result
        return magic


class Observer(ABC):
    """An observer for observing a observable

    Implement `update` to handle notifications
    """
    
    @abstractmethod
    def update(self, observable):
        """Handle a update notification from an object that is being observed by this object.

        :param observable: Object that sent the notification
        :type observable: Observable
        """
        raise NotImplementedError