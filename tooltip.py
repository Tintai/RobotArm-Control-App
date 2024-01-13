#   tooltip.py
#   RobotArm Control v1.0 Tintai

import tkinter as tk

class CreateToolTip:
    def __init__(self, widget, text):
        self.waittime = 1000  # milliseconds
        self.wraplength = 180  # pixels
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.id = None
        self.x = self.y = 0

        self.hook()

    def hook(self):
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.motion)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hide()

    def motion(self, event=None):
        self.x, self.y = event.x_root + 25, event.y_root + 20

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self):
        if self.tooltip:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1, wraplength=self.wraplength)
        label.pack(ipadx=1)

    def hide(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
