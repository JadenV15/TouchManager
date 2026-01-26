import tkinter as tk
import tkinter.ttk as ttk

class Tooltip:
    """A class for creating simple, IDLE-style tooltips"""
    def __init__(self,
                 widget,
                 *,
                 bg='#FFFFEA',
                 pad=(5, 3, 5, 3),
                 text='widget info',
                 waittime=400,
                 wraplength=250):

        self.waittime = waittime
        self.wraplength = wraplength
        self.widget = widget
        self.text = text
        self.bg = bg
        self.pad = pad
        self.id = None
        self.tw = None
        
        self.remove() # unbind any old callbacks
        self.bind()
        
    def bind(self):
        self.widget.bind("<Enter>", self.onEnter)
        self.widget.bind("<Leave>", self.onLeave)
        self.widget.bind("<ButtonPress>", self.onLeave)

    def onEnter(self, event=None):
        self.schedule()

    def onLeave(self, event=None):
        self.unschedule()
        self.hide()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def show(self):
        def tip_pos_calculator(widget, label,
                               *,
                               tip_delta=(10, 5), pad=(5, 3, 5, 3)):

            s_width, s_height = widget.winfo_screenwidth(), widget.winfo_screenheight()
            width = pad[0] + label.winfo_reqwidth() + pad[2]
            height = pad[1] + label.winfo_reqheight() + pad[3]

            mouse_x, mouse_y = widget.winfo_pointerxy()
            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            x2, y2 = x1 + width, y1 + height

            if x2 > s_width:
                x1 = mouse_x - tip_delta[0] - width
            if y2 > s_height:
                y1 = mouse_y - tip_delta[1] - height
            if y1 < 0:
                y1 = 0

            return x1, y1
        
        if self.tw:
            return
        
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.attributes("-topmost", True)

        frame = tk.Frame(self.tw, background=self.bg, borderwidth=0)
        label = tk.Label(
            frame,
            text=self.text,
            justify=tk.LEFT,
            background=self.bg,
            relief=tk.SOLID,
            borderwidth=0,
            wraplength=self.wraplength
        )

        label.grid(padx=(self.pad[0], self.pad[2]),
                   pady=(self.pad[1], self.pad[3]))
        frame.grid()

        x, y = tip_pos_calculator(self.widget, label)
        self.tw.wm_geometry(f"+{x}+{y}")

    def hide(self):
        if self.tw:
            self.tw.destroy()
        self.tw = None
    
    # caller functions
    
    def set_text(self, text):
        """Set new tooltip text"""
        self.text = text
    
    def remove(self):
        """Remove the tooltip from the widget"""
        self.unschedule()
        self.hide()
        self.widget.unbind("<Enter>")
        self.widget.unbind("<Leave>")
        self.widget.unbind("<ButtonPress>")
    

if __name__ == '__main__':
    pass