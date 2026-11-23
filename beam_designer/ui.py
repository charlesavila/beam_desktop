"""Desktop forms and state coordination; no engineering formulas live here."""
import math
import tkinter as tk
from tkinter import ttk
from .models import Beam, Properties, PointLoad, UniformLoad, ValidationIssue
from .catalog import SECTIONS, MATERIALS, SPEC_EXAMPLES
from .validation import validate
from .analysis import analyze
from .diagrams import Diagrams, decorate


class ScrollFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg="#f7f0ff", highlightthickness=0)
        self.canvas.configure(yscrollincrement=1)
        self.scroll_remainder = 0.0
        self.windowing_system = self.tk.call("tk", "windowingsystem")
        bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window, width=e.width))
        # A panel-specific bind tag runs before Entry/Combobox/Scrollbar classes,
        # so children scroll their panel without changing a selected member.
        self.scroll_tag = f"BeamScroll{id(self)}"
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind_class(self.scroll_tag, sequence, self.wheel)
        try:
            self.bind_class(self.scroll_tag, "<TouchpadScroll>", self.touchpad)
        except tk.TclError:
            pass  # Tk 8.6 delivers trackpad gestures as MouseWheel instead.
        self.winfo_toplevel().bind("<Map>", self.tag_widget, add="+")
        self.tag_tree(self)

    def tag_widget(self, event):
        widget = event.widget
        ancestor = widget
        while isinstance(ancestor, tk.Misc):
            if ancestor is self:
                tags = widget.bindtags()
                if self.scroll_tag not in tags:
                    widget.bindtags((self.scroll_tag,) + tags)
                return
            ancestor = getattr(ancestor, "master", None)

    def tag_tree(self, widget):
        # Also supports initially withdrawn windows and widgets added at runtime.
        from types import SimpleNamespace
        self.tag_widget(SimpleNamespace(widget=widget))
        for child in widget.winfo_children():
            self.tag_tree(child)

    def scroll_pixels(self, pixels):
        if pixels and self.scroll_remainder * pixels < 0:
            self.scroll_remainder = 0.0
        self.scroll_remainder += pixels
        whole = math.trunc(self.scroll_remainder)
        self.scroll_remainder -= whole
        if whole:
            self.canvas.yview_scroll(whole, "units")
        return "break"

    def wheel(self, event):
        number = getattr(event, "num", None)
        if number in (4, 5):
            return self.scroll_pixels(-36 if number == 4 else 36)
        delta = event.delta
        return self.scroll_pixels(-delta * (3 if self.windowing_system == "aqua" else 36/120))

    def touchpad(self, event):
        # Tk packs signed horizontal/vertical pixel deltas into a single integer.
        _, vertical = self.tk.call("tk::PreciseScrollDeltas", event.delta)
        return self.scroll_pixels(-float(vertical))


class Application:
    def __init__(self, root):
        self.root = root
        self.suspended = True
        self.pending = None
        self.fields = {}
        self.loads = []
        root.title("Beam Designer | Flower Power Engineering")
        root.geometry("1280x920")
        root.minsize(1040, 700)
        root.configure(bg="#f7f0ff")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background="#f7f0ff", foreground="#302248")
        style.configure("TFrame", background="#f7f0ff")
        style.configure("TLabelframe", background="#f7f0ff", bordercolor="#c9b2e5")
        style.configure("TLabelframe.Label", font=("Segoe UI", 11, "bold"), foreground="#7946bf")
        style.configure("TButton", padding=(9, 6), background="#e3d0f4")
        style.configure("Accent.TButton", background="#7946bf", foreground="white")
        style.map("Accent.TButton", background=[("active", "#6235a0")])
        style.configure("Invalid.TEntry", fieldbackground="#ffe1e7", bordercolor="#b82e53")
        style.configure("Error.TLabel", foreground="#b02c48", font=("Segoe UI", 9))
        header = tk.Canvas(root, height=78, bg="#f8eaff", highlightthickness=0)
        header.pack(fill="x")
        header.bind("<Configure>", lambda e: decorate(header, e.width))
        toolbar = ttk.Frame(root, padding=(16, 6))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Calculate", style="Accent.TButton", command=self.calculate).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Reset example", command=self.reset).pack(side="left", padx=3)
        ttk.Label(toolbar, text="Spec examples:").pack(side="left", padx=(18, 5))
        self.example_choice = tk.StringVar(value=next(iter(SPEC_EXAMPLES)))
        ttk.Combobox(toolbar, textvariable=self.example_choice, values=tuple(SPEC_EXAMPLES),
                     state="readonly", width=40).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Load example", command=lambda: self.load_example(self.example_choice.get())).pack(side="left", padx=3)
        # Give both panes real minimum widths. Setting a ttk sash in after_idle
        # can run before the window is allocated and permanently collapse the
        # zero-weight input pane to one pixel on first launch.
        panes = tk.PanedWindow(root, orient="horizontal", sashwidth=8,
                               background="#dfd0ed", borderwidth=0,
                               opaqueresize=True)
        self.panes = panes
        panes.pack(fill="both", expand=True, padx=12, pady=8)
        self.input_scroll, output_scroll = ScrollFrame(panes), ScrollFrame(panes)
        self.output_scroll = output_scroll
        panes.add(self.input_scroll, minsize=340, width=370, stretch="never")
        panes.add(output_scroll, minsize=520, stretch="always")
        form = self.input_scroll.body
        box = ttk.LabelFrame(form, text="01 / Beam & supports", padding=10)
        box.pack(fill="x", padx=6, pady=6)
        self.field(box, "support", "Support type", "Simply supported", ("Simply supported", "Cantilever"))
        self.field(box, "span", "Span [ft]", "20")
        box = ttk.LabelFrame(form, text="02 / Section & material", padding=10)
        box.pack(fill="x", padx=6, pady=6)
        self.field(box, "section", "Member (strong axis)", "W12x26", tuple(SECTIONS)+("Custom",))
        self.field(box, "material", "Material preset", "Steel (example)", tuple(MATERIALS)+("Custom",))
        self.field(box, "inertia", "I [in^4]", "204")
        self.field(box, "section_modulus", "S [in^3]", "33.4")
        self.field(box, "elasticity", "E [ksi]", "29000")
        self.field(box, "allowable_stress", "Allowable bending F_b [ksi]", "30")
        ttk.Label(box, text="All numeric values are editable. Enter numbers in\nthe units shown; property edits select Custom.",
                  wraplength=290, foreground="#74617f", font=("Segoe UI", 9)).pack(anchor="w", pady=5)
        self.fields["section"][0].trace_add("write", self.section_changed)
        self.fields["material"][0].trace_add("write", self.material_changed)
        for key in ("inertia", "section_modulus", "elasticity", "allowable_stress"):
            self.fields[key][0].trace_add("write", lambda *_, name=key: self.property_changed(name))
        self.load_box = ttk.LabelFrame(form, text="03 / Loads (downward positive)", padding=8)
        self.load_box.pack(fill="x", padx=6, pady=6)
        buttons = ttk.Frame(self.load_box)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="+ Point", command=lambda: self.add_load("Point")).pack(side="left", padx=2)
        ttk.Button(buttons, text="+ Uniform", command=lambda: self.add_load("Uniform")).pack(side="left", padx=2)
        self.rows = ttk.Frame(self.load_box)
        self.rows.pack(fill="x")
        ttk.Label(form, text="Auto-calculates after valid edits.\nCantilever is fixed at the left end.",
                  padding=9, foreground="#74617f").pack(anchor="w")
        self.summary = ttk.LabelFrame(output_scroll.body, text="Results / the governing values", padding=12)
        self.summary.pack(fill="x", padx=8, pady=6)
        self.status = ttk.Label(self.summary, font=("Segoe UI", 11, "bold"))
        self.status.pack(anchor="w")
        self.reactions = ttk.Label(self.summary, wraplength=630)
        self.reactions.pack(anchor="w", pady=3)
        self.extrema = ttk.Label(self.summary, wraplength=630)
        self.extrema.pack(anchor="w", pady=3)
        self.bending = ttk.Label(self.summary, font=("Segoe UI", 10, "bold"), wraplength=630)
        self.bending.pack(anchor="w", pady=3)
        self.displacement = ttk.Label(self.summary, font=("Segoe UI", 10, "bold"), wraplength=630)
        self.displacement.pack(anchor="w", pady=3)
        self.summary.bind("<Configure>", lambda e: [label.configure(wraplength=max(250, e.width-32))
                           for label in (self.reactions, self.extrema, self.bending, self.displacement)])
        self.diagrams = Diagrams(output_scroll.body)
        self.diagrams.pack(fill="x", expand=True)
        self.input_scroll.tag_tree(self.input_scroll)
        self.output_scroll.tag_tree(self.output_scroll)
        self.suspended = False
        self.reset()

    def field(self, parent, key, label, initial, choices=None):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=3)
        ttk.Label(frame, text=label).pack(anchor="w")
        var = tk.StringVar(value=initial)
        if choices:
            widget = ttk.Combobox(frame, textvariable=var, values=choices, state="readonly", width=24)
        else:
            widget = ttk.Entry(frame, textvariable=var, width=24)
        widget.pack(fill="x")
        error = ttk.Label(frame, text="", style="Error.TLabel", wraplength=285)
        self.fields[key] = (var, widget, error)
        var.trace_add("write", self.changed)
        self.input_scroll.tag_tree(frame)
        return var

    def section_changed(self, *_):
        if self.suspended:
            return
        selected = self.fields["section"][0].get()
        if selected in SECTIONS:
            inertia, modulus, material = SECTIONS[selected]
            self.suspended = True
            try:
                self.fields["inertia"][0].set(str(inertia))
                self.fields["section_modulus"][0].set(str(modulus))
                self.fields["material"][0].set(material)
                e, fb = MATERIALS[material]
                self.fields["elasticity"][0].set(str(e))
                self.fields["allowable_stress"][0].set(str(fb))
            finally:
                self.suspended = False
        self.changed()

    def material_changed(self, *_):
        if self.suspended:
            return
        selected = self.fields["material"][0].get()
        if selected in MATERIALS:
            e, fb = MATERIALS[selected]
            self.suspended = True
            try:
                self.fields["elasticity"][0].set(str(e))
                self.fields["allowable_stress"][0].set(str(fb))
            finally:
                self.suspended = False
        self.changed()

    def property_changed(self, key):
        if self.suspended:
            return
        selector = "section" if key in ("inertia", "section_modulus") else "material"
        self.fields[selector][0].set("Custom")

    def add_load(self, kind, values=None):
        i = len(self.loads)
        frame = ttk.LabelFrame(self.rows, text=f"{i+1}. {kind} load", padding=6)
        frame.pack(fill="x", pady=6)
        ttk.Button(frame, text="Remove", command=lambda f=frame: self.remove_load(f)).pack(anchor="e")
        if values is None:
            values = ["0", "0"] if kind == "Point" else ["0", "0", self.fields["span"][0].get()]
        names = [("magnitude", "Magnitude [kips]"), ("position", "Position [ft]")] if kind == "Point" else [
            ("magnitude", "Magnitude [kip/ft]"), ("start", "Start [ft]"), ("end", "End [ft]")]
        keys = []
        for (name, label), value in zip(names, values):
            key = f"loads.{i}.{name}"
            self.field(frame, key, label, value)
            keys.append(key)
        self.loads.append((kind, frame, keys))
        self.input_scroll.tag_tree(frame)
        self.changed()

    def remove_load(self, frame):
        remaining = [(kind, [self.fields[k][0].get() for k in keys])
                     for kind, f, keys in self.loads if f != frame]
        self.suspended = True
        self.clear_loads()
        for kind, values in remaining:
            self.add_load(kind, values)
        self.suspended = False
        self.changed()

    def clear_loads(self):
        for _, frame, keys in self.loads:
            frame.destroy()
            for key in keys:
                del self.fields[key]
        self.loads.clear()

    def reset(self):
        self.load_example(next(iter(SPEC_EXAMPLES)))

    def load_example(self, name):
        beam = SPEC_EXAMPLES[name]
        self.example_choice.set(name)
        self.suspended = True
        self.clear_loads()
        for key, value in {"support": beam.support, "span": str(beam.span), "section": "W12x26",
                           "material": "Steel (example)", "inertia": str(beam.properties.inertia),
                           "section_modulus": str(beam.properties.section_modulus),
                           "elasticity": str(beam.properties.elasticity),
                           "allowable_stress": str(beam.properties.allowable_stress)}.items():
            self.fields[key][0].set(value)
        for load in beam.loads:
            if isinstance(load, PointLoad):
                self.add_load("Point", [str(load.magnitude), str(load.position)])
            else:
                self.add_load("Uniform", [str(load.magnitude), str(load.start), str(load.end)])
        self.suspended = False
        self.calculate()
        self.input_scroll.canvas.yview_moveto(0)

    def changed(self, *_):
        if self.suspended:
            return
        if self.pending:
            self.root.after_cancel(self.pending)
        # Invalidate output immediately; only rendering/reanalysis is debounced.
        self.clear_result("INCOMPLETE / editing inputs")
        self.pending = self.root.after(180, self.calculate)

    def clear_result(self, status):
        self.status.configure(text=status, foreground="#a33256")
        for label in (self.reactions, self.extrema, self.bending, self.displacement):
            label.configure(text="")
        self.diagrams.set_result()

    def calculate(self):
        if self.pending:
            self.root.after_cancel(self.pending)
            self.pending = None
        parse_issues = []
        for var, widget, error in self.fields.values():
            if isinstance(widget, ttk.Entry) and not isinstance(widget, ttk.Combobox):
                widget.configure(style="TEntry")
            error.pack_forget()

        def number(key):
            text = self.fields[key][0].get().strip()
            try:
                value = float(text)
                if not math.isfinite(value):
                    raise ValueError
                return value
            except ValueError:
                parse_issues.append(ValidationIssue(key, "Required." if not text else "Enter a finite number."))
                return math.nan

        span = number("span")
        props = Properties(*(number(k) for k in ("inertia", "section_modulus", "elasticity", "allowable_stress")))
        loads = []
        for kind, _, keys in self.loads:
            args = [number(k) for k in keys]
            loads.append(PointLoad(*args) if kind == "Point" else UniformLoad(*args))
        beam = Beam(span, self.fields["support"][0].get(), props, tuple(loads))
        issues = parse_issues + validate(beam)
        if issues:
            seen = set()
            for issue in issues:
                if issue.field not in self.fields or issue.field in seen:
                    continue
                seen.add(issue.field)
                _, widget, error = self.fields[issue.field]
                widget.configure(style="Invalid.TEntry")
                error.configure(text=issue.message)
                error.pack(anchor="w")
            incomplete = any(i.message == "Required." for i in parse_issues)
            self.clear_result("INCOMPLETE / fill required fields" if incomplete else "INVALID / check highlighted fields")
            return
        try:
            result = analyze(beam)
        except (ValueError, OverflowError, ZeroDivisionError) as exc:
            self.clear_result(f"INVALID / {exc}")
            return
        self.status.configure(text="Analysis complete", foreground="#087f85")
        if beam.support == "Simply supported":
            reaction_text = f"Reactions (up): left {result.left_reaction:.2f} kips  |  right {result.right_reaction:.2f} kips"
        else:
            reaction_text = f"Fixed reaction: {result.left_reaction:.2f} kips up  |  fixed moment {result.fixed_moment:.2f} kip-ft CCW"
        self.reactions.configure(text=reaction_text)
        self.extrema.configure(text=(f"Max |V|: {abs(result.max_shear.value):.2f} kips @ {result.max_shear.location:.2f} ft\n"
                                     f"Max |M|: {abs(result.governing_moment.value):.2f} kip-ft @ {result.governing_moment.location:.2f} ft\n"
                                     f"Max |deflection|: {abs(result.max_deflection.value):.3f} in @ {result.max_deflection.location:.2f} ft"))
        for label, passed, text in (
            (self.bending, result.bending_pass, f"Bending: {result.stress:.2f} / {props.allowable_stress:.2f} ksi allowable"),
            (self.displacement, result.deflection_pass, f"Deflection: {abs(result.max_deflection.value):.3f} / {result.deflection_limit:.3f} in (L/360)")):
            label.configure(text=f"{'[OK] PASS' if passed else '[X] FAIL'}  |  {text}",
                            foreground="#087f85" if passed else "#b02c48")
        self.diagrams.set_result(beam, result)


def launch():
    root = tk.Tk()
    Application(root)
    root.mainloop()
