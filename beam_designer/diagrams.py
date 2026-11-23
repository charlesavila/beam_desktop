"""Tkinter Canvas drawings. All engineering values come from analysis.py."""
import math
import tkinter as tk
from .models import PointLoad

INK = "#302248"
PURPLE = "#7946bf"
PINK = "#cf397e"
TEAL = "#087f85"


def decorate(canvas, width):
    """Draw the locally generated flower and rainbow header."""
    canvas.delete("all")
    for i, color in enumerate(("#f26883", "#ffaf4a", "#ffe667", "#84c99d", "#76b7db", "#ac8adb")):
        canvas.create_arc(width-235+i*9, 5+i*9, width+25-i*9, 255-i*9,
                          start=0, extent=180, style="arc", width=9, outline=color)
    for cx, cy in ((28, 37), (width-25, 31)):
        for i in range(8):
            a = i*math.pi/4
            x, y = cx+13*math.cos(a), cy+13*math.sin(a)
            canvas.create_oval(x-7, y-7, x+7, y+7, fill="#ef81b5", outline="")
        canvas.create_oval(cx-7, cy-7, cx+7, cy+7, fill="#ffe667", outline="")
    canvas.create_text(64, 24, text="Beam Designer", anchor="w", font=("Georgia", 23, "bold"), fill=INK)
    canvas.create_text(66, 52, text="A little flower power. A lot of beam power.", anchor="w",
                       font=("Segoe UI", 10), fill=INK)


class Diagrams(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f7f0ff")
        self.beam = self.result = None
        self.canvases = []
        for height in (220, 175, 175, 175):
            c = tk.Canvas(self, height=height, bg="#fffdf7", highlightthickness=1,
                          highlightbackground="#dfd0ed")
            c.pack(fill="x", padx=8, pady=5)
            c.bind("<Configure>", lambda event: self.redraw())
            self.canvases.append(c)

    def set_result(self, beam=None, result=None):
        self.beam, self.result = beam, result
        self.redraw()

    def redraw(self):
        for canvas in self.canvases:
            canvas.delete("all")
        if self.result is None:
            for canvas, title in zip(self.canvases, ("Beam", "Shear", "Moment", "Deflection")):
                canvas.create_text(20, 24, text=title, anchor="w", fill=INK,
                                   font=("Segoe UI", 12, "bold"))
                canvas.create_text(20, 62, text="Complete valid inputs to display results.",
                                   anchor="w", fill="#776783")
            return
        self.draw_beam()
        self.draw_plot(self.canvases[1], "Shear", "kips", "shear", TEAL, 2)
        self.draw_plot(self.canvases[2], "Moment", "kip-ft", "moment", PURPLE, 2)
        self.draw_plot(self.canvases[3], "Deflection (+ up)", "in", "deflection", PINK, 3)

    def draw_beam(self):
        c = self.canvases[0]
        b, r = self.beam, self.result
        height = max(220, 130+len(b.loads)*26)
        if int(float(c.cget("height"))) != height:
            c.configure(height=height)
        left, right = 80, max(300, c.winfo_width()-50)
        y = height-82
        x = lambda position: left+(right-left)*position/b.span
        c.create_text(18, 19, text="Beam & loading", anchor="w", fill=INK,
                      font=("Segoe UI", 12, "bold"))
        c.create_line(left, y, right, y, width=7, fill=INK)
        for i, load in enumerate(b.loads):
            top = 48+i*26
            if isinstance(load, PointLoad):
                px = x(load.position)
                c.create_line(px, top+12, px, y-5, fill=PINK, width=2, arrow="last")
                text = f"P{i+1}: {load.magnitude:.2f} k @ {load.position:.2f} ft"
                c.create_text(min(max(px, left+80), right-80), top, text=text, fill=PINK,
                              font=("Segoe UI", 9))
            else:
                xa, xb = x(load.start), x(load.end)
                c.create_line(xa, top+10, xb, top+10, fill=PURPLE, width=2)
                for j in range(9):
                    px = xa+(xb-xa)*j/8
                    c.create_line(px, top+10, px, y-6, arrow="last", fill=PURPLE)
                text = f"U{i+1}: {load.magnitude:.2f} k/ft, {load.start:.2f}-{load.end:.2f} ft"
                c.create_text((left+right)/2, top, text=text, fill=PURPLE, font=("Segoe UI", 9))
        if b.support == "Cantilever":
            c.create_line(left-4, y-23, left-4, y+23, width=5, fill=INK)
            for dy in range(-22, 24, 7):
                c.create_line(left-4, y+dy, left-17, y+dy+9, fill=INK)
            c.create_text(left+5, y+44, anchor="w", text=f"R = {r.left_reaction:.2f} k;  M = {r.fixed_moment:.2f} kip-ft CCW",
                          fill=TEAL, font=("Segoe UI", 9))
        else:
            for px in (left, right):
                c.create_polygon(px, y+4, px-12, y+23, px+12, y+23,
                                 outline=INK, fill="#ffe7a7", width=2)
            for dx in (-7, 7):
                c.create_oval(right+dx-3, y+24, right+dx+3, y+30, outline=INK)
            c.create_text(left, y+47, text=f"R = {r.left_reaction:.2f} k", fill=TEAL)
            c.create_text(right, y+47, text=f"R = {r.right_reaction:.2f} k", fill=TEAL)
        for px in ((left,) if b.support == "Cantilever" else (left, right)):
            c.create_line(px, y+45, px, y+8, arrow="last", fill=TEAL, width=2)
        c.create_text((left+right)/2, height-12, text=f"Span {b.span:.2f} ft   |   x measured from left", fill=INK)

    def draw_plot(self, c, title, unit, attr, color, decimals):
        result, span = self.result, self.beam.span
        left, right, zero = 80, max(300, c.winfo_width()-50), 96
        values = [getattr(s, attr) for s in result.samples]
        peak = max(abs(v) for v in values)
        scale = 41/peak if peak else 1
        c.create_text(18, 18, text=f"{title} [{unit}]", anchor="w", fill=color,
                      font=("Segoe UI", 11, "bold"))
        c.create_line(left, 47, left, 140, fill="#b7a8c5", arrow="first")
        c.create_line(left, zero, right, zero, fill="#b7a8c5", dash=(3, 3))
        c.create_text(left-9, zero, text="0", anchor="e", fill=INK)
        points = []
        for s, value in zip(result.samples, values):
            points.extend((left+(right-left)*s.x/span, zero-value*scale))
        c.create_line(*points, fill=color, width=2)
        candidates = [result.max_shear] if attr == "shear" else (
            [result.max_moment, result.min_moment] if attr == "moment" else [result.max_deflection])
        text = "   |   ".join(f"{v.value:.{decimals}f} {unit} @ {v.location:.2f} ft" for v in candidates)
        c.create_text(left, 39, text=text, anchor="w", fill=INK, font=("Segoe UI", 9))
        for v in candidates:
            px, py = left+(right-left)*v.location/span, zero-v.value*scale
            c.create_oval(px-3, py-3, px+3, py+3, fill=color, outline="")
        c.create_text(left, 156, text="0.00", fill=INK)
        c.create_text(right, 156, text=f"{span:.2f}", fill=INK)
        c.create_text((left+right)/2, 156, text="Position x [ft]", fill=INK)
