"""Optional hidden-window integration check: python tests/ui_smoke.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tkinter as tk
from beam_designer.ui import Application
from beam_designer.catalog import SPEC_EXAMPLES


def check_scrolling(app, root):
    """Generate real Tk events on children, including dropdowns and canvases."""
    for panel, target in ((app.input_scroll, app.fields['support'][1]),
                          (app.output_scroll, app.diagrams.canvases[1])):
        panel.tag_tree(panel)
        panel.canvas.configure(scrollregion=(0, 0, 800, 10000))
        panel.canvas.yview_moveto(0)
        start = panel.canvas.yview()[0]
        for _ in range(20):
            target.event_generate('<MouseWheel>', delta=-1)
        root.update()
        assert panel.canvas.yview()[0] > start, 'Small wheel deltas were lost'
        before = panel.canvas.yview()[0]
        # Tk 9 high-resolution deltas: x in high 16 bits, y in low 16 bits.
        try:
            target.event_generate('<TouchpadScroll>', delta=(20 << 16) | ((-8) & 0xffff))
        except tk.TclError as exc:
            if 'bad event type' not in str(exc):
                raise
        else:
            root.update()
            assert panel.canvas.yview()[0] > before, 'Trackpad gesture did not scroll'
            before = panel.canvas.yview()[0]
            target.event_generate('<TouchpadScroll>', delta=20 << 16)
            root.update()
            assert panel.canvas.yview()[0] == before, 'Horizontal motion scrolled vertically'
            target.event_generate('<TouchpadScroll>', delta=8)
            root.update()
            assert panel.canvas.yview()[0] < before, 'Upward trackpad gesture did not scroll'
    assert app.fields['support'][0].get() == 'Simply supported'


def check_spec_inputs(app):
    for name, expected_moment in zip(SPEC_EXAMPLES, (50, 50, 100, 50, 37.5)):
        app.load_example(name)
        assert abs(abs(app.diagrams.result.governing_moment.value)-expected_moment) < 1e-8

    # Enter case 2 through the same editable widgets a person uses, starting
    # with the example's old uniform load removed.
    app.reset()
    app.remove_load(app.loads[0][1])
    entry = app.fields['span'][1]
    entry.delete(0, 'end')
    entry.insert(0, '10')
    app.add_load('Point')
    for field, value in (('magnitude', '20'), ('position', '5')):
        entry = app.fields[f'loads.0.{field}'][1]
        entry.delete(0, 'end')
        entry.insert(0, value)
    app.calculate()
    assert app.diagrams.result.governing_moment.value == 50
    assert app.diagrams.result.left_reaction == 10

    # Direct property entry must work without finding a separate unlock option.
    for key, value in (('inertia', '300'), ('section_modulus', '40'),
                       ('elasticity', '29000'), ('allowable_stress', '25')):
        entry = app.fields[key][1]
        assert str(entry.cget('state')) == 'normal'
        entry.delete(0, 'end')
        entry.insert(0, value)
    app.calculate()
    assert app.fields['section'][0].get() == 'Custom'
    assert app.fields['material'][0].get() == 'Custom'
    assert app.diagrams.result.stress == 15


def check():
    root = tk.Tk()
    root.withdraw()
    failures = []
    root.report_callback_exception = lambda kind, value, tb: failures.append(value)
    try:
        app = Application(root)
        root.update()
        assert app.status.cget('text') == 'Analysis complete'
        assert '[OK] PASS' in app.bending.cget('text')
        assert '0.609' in app.displacement.cget('text')
        assert all(c.find_all() for c in app.diagrams.canvases)
        check_scrolling(app, root)
        check_spec_inputs(app)
        app.reset()

        app.fields['span'][0].set('')
        assert app.diagrams.result is None  # No stale results while typing.
        app.calculate()
        assert app.status.cget('text').startswith('INCOMPLETE')
        assert app.fields['span'][2].cget('text') == 'Required.'
        assert not app.bending.cget('text')
        app.fields['span'][0].set('20')
        app.fields['loads.0.end'][0].set('21')
        app.calculate()
        assert app.status.cget('text').startswith('INVALID')
        assert app.fields['loads.0.end'][2].cget('text')

        app.reset()
        app.fields['support'][0].set('Cantilever')
        app.calculate()
        assert app.diagrams.result.fixed_moment == 200
        assert app.diagrams.result.governing_moment.location == 0

        app.add_load('Point', ['3', '10'])
        app.calculate()
        assert app.diagrams.result.left_reaction == 23
        app.remove_load(app.loads[0][1])
        app.calculate()
        assert len(app.loads) == 1
        assert app.diagrams.result.left_reaction == 3
        app.remove_load(app.loads[0][1])
        app.calculate()
        assert app.diagrams.result.max_deflection.value == 0

        app.fields['section'][0].set('Lumber 2x10')
        app.calculate()
        assert app.fields['material'][0].get() == 'Lumber (example)'
        assert app.fields['elasticity'][0].get() == '1600.0'
        app.fields['section'][0].set('Custom')
        app.fields['inertia'][0].set('0')
        app.calculate()
        assert app.status.cget('text').startswith('INVALID')

        app.reset()
        # Exercise canvas rendering at the supported desktop dimensions.
        for width in (530, 850):
            for canvas in app.diagrams.canvases:
                canvas.configure(width=width)
            root.update()
            app.diagrams.redraw()
        assert app.status.cget('text') == 'Analysis complete'
        assert not failures, failures
        print('UI smoke check passed: spec inputs, five examples, direct properties, wheel/trackpad events, startup, validation, reset, loads, materials, diagrams.')
    finally:
        root.destroy()


if __name__ == '__main__':
    check()
