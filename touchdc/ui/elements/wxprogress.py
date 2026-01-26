"""Experimental: nicer wx progress bars in tkinter apps"""
__all__ = ['Progress']

import wx
from threading import Thread
import queue

class _Indeterminate(wx.Gauge):
    def __init__(self, parent, orient=wx.HORIZONTAL, length=300):
        style = wx.GA_HORIZONTAL if orient == wx.HORIZONTAL else wx.GA_VERTICAL
        super().__init__(parent, range=100, style=style, size=(length, -1))

class _Progress(wx.Dialog):
    def __init__(
        self,
        parent=None,
        title="Progress",
        message="Loading",
        center=True,
        speed=10,
        lock=True,
        minsize=(360, 120),
        *args,
        **kw
    ):
        style = wx.DEFAULT_DIALOG_STYLE | wx.BORDER_SIMPLE
        if lock:
            style |= wx.STAY_ON_TOP

        super().__init__(parent, title=title, style=style, *args, **kw)

        panel = wx.Panel(self)

        align = wx.ALIGN_CENTER if center else wx.ALIGN_LEFT
        self.message = wx.StaticText(panel, label=message, style=align)

        self.bar = _Indeterminate(panel)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.message, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self.bar, 0, wx.ALL | wx.EXPAND, 12)

        panel.SetSizer(sizer)

        self.SetMinSize(minsize)
        self.Fit()
        self.CentreOnScreen()

        # Indeterminate animation
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_pulse, self.timer)
        self.timer.Start(speed)

        if lock:
            self.Bind(wx.EVT_CLOSE, lambda evt: None)
            self.ShowModal()
        else:
            self.Show()

    def _on_pulse(self, event):
        self.bar.Pulse()

    def close(self):
        self.timer.Stop()
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        self.Destroy()

class Progress(Thread):
    def __init__(self, *args, **kw):
        self.q = queue.Queue()
        self.timeout = 0.1
        self.interval = 0.5
        self.p_args = args
        self.p_kw = kw
        
        super().__init__(target=self.run, daemon=True)
    
    def on_thread(self, func, *args, **kw):
        self.q.put((func, args, kw))
    
    def run(self):
        print('debug')
        def poll():
            try:
                unbound, args, kw = self.q.get(timeout=self.timeout)
                getattr(progress, unbound.__name__)(*args, **kw)
            except queue.Empty:
                wx.CallLater(self.interval, poll)
        
        print('debug')
        
        app = wx.App()
        
        progress = _Progress(*self.p_args, **self.p_kw)
        print('debug')
        
        wx.CallLater(1, poll)
        
        print('mainloop')
        app.MainLoop()
        
    def close(self):
        self.on_thread(_Progress.close)
        

if __name__ == "__main__":
    progress = Progress(
        title="Working",
        message="Please wait…",
        lock=True
    )
    
    progress.start()
