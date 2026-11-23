"""Mapped-window regression: exercise focus and real Tk keyboard bindings."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tkinter as tk
from beam_designer.ui import Application
from beam_designer.catalog import SPEC_EXAMPLES
from beam_designer.models import PointLoad


def reveal(root, app, widget):
    panel = app.input_scroll
    root.update_idletasks()
    top = widget.winfo_y()
    parent = widget.master
    while parent is not panel.body:
        top += parent.winfo_y()
        parent = parent.master
    panel.canvas.yview_moveto(max(0, top-70)/panel.body.winfo_height())
    root.update()
    cx, cy = widget.winfo_rootx()+8, widget.winfo_rooty()+8
    assert root.winfo_containing(cx, cy) == widget, f'{widget} is not reachable by mouse'


def enter(root, app, key, value):
    widget = app.fields[key][1]
    reveal(root, app, widget)
    type_value(root, widget, value)


def wait_for_calculation(root):
    root.after(230, root.quit)
    root.mainloop()


def type_value(root, entry, value):
    """Click and type using events, without Entry.insert or StringVar.set."""
    entry.event_generate('<ButtonPress-1>', x=8, y=8)
    entry.event_generate('<ButtonRelease-1>', x=8, y=8)
    root.update()
    assert root.focus_get() == entry, f'Click did not focus {entry}'
    entry.event_generate('<<SelectAll>>')
    entry.event_generate('<KeyPress>', keysym='BackSpace')
    for char in value:
        entry.event_generate('<KeyPress>', keysym={'.': 'period', '-': 'minus'}.get(char, char))
    root.update()
    assert entry.get() == value, f'Keyboard entry failed: expected {value!r}, got {entry.get()!r}'


def check():
    root = tk.Tk()
    root.withdraw()
    # A transparent window is skipped by Windows hit testing. Map a real window
    # briefly so pointer hit testing checks what a user can actually click.
    root.attributes('-topmost', True)
    failures = []
    root.report_callback_exception = lambda kind, value, tb: failures.append(value)
    try:
        app = Application(root)
        root.deiconify()
        root.update()
        root.focus_force()
        root.update()
        for geometry in ('1280x845', '1040x700'):
            root.geometry(geometry)
            root.update()
            # The original first-launch failure had a one-pixel canvas viewport.
            assert app.input_scroll.canvas.winfo_width() >= 300
            assert app.input_scroll.canvas.winfo_height() >= 400
            for key in ('span', 'inertia', 'section_modulus', 'elasticity', 'allowable_stress',
                        'loads.0.magnitude', 'loads.0.start', 'loads.0.end'):
                enter(root, app, key, '25' if key == 'span' else app.fields[key][0].get())
            app.panes.sash_place(0, 0, 0)
            root.update()
            assert app.input_scroll.canvas.winfo_width() >= 300, 'Divider hid the inputs'
            app.panes.sash_place(0, 370, 0)
            root.update()

        # Re-enter every spec case with keyboard events, rather than loading its
        # numeric values through the model or Entry.insert.
        for beam, moment in zip(SPEC_EXAMPLES.values(), (50, 50, 100, 50, 37.5)):
            app.reset()
            app.remove_load(app.loads[0][1])
            app.fields['support'][0].set(beam.support)
            enter(root, app, 'span', str(beam.span))
            for i, load in enumerate(beam.loads):
                if isinstance(load, PointLoad):
                    app.add_load('Point')
                    inputs = (('magnitude', load.magnitude), ('position', load.position))
                else:
                    app.add_load('Uniform')
                    inputs = (('magnitude', load.magnitude), ('start', load.start), ('end', load.end))
                for field, value in inputs:
                    enter(root, app, f'loads.{i}.{field}', str(value))
            wait_for_calculation(root)
            assert app.diagrams.result is not None, app.status.cget('text')
            assert abs(abs(app.diagrams.result.governing_moment.value)-moment) < 1e-8

        enter(root, app, 'loads.0.end', '99')
        wait_for_calculation(root)
        assert app.diagrams.result is None
        assert app.status.cget('text').startswith('INVALID')
        enter(root, app, 'loads.0.end', '15')
        wait_for_calculation(root)
        assert app.diagrams.result is not None
        assert not failures, failures
        print('PASS: input panel visible at startup and minimum size; divider cannot hide inputs; '
              'all numeric fields accept clicks/keystrokes; all five spec cases typed and '
              'auto-calculated; invalid load clears results and valid correction restores them.')
    finally:
        root.destroy()


if __name__ == '__main__':
    check()
