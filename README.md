# Beam Designer

A local Python Tkinter desktop application for simply supported and left-fixed
cantilever beams, with combined downward point and uniform loads. Uses only the
Python standard library; no packages, network connection, or build step required.

## Run

Install Python 3.10 or newer with Tcl/Tk support (included in the standard Windows
Python installer), open a terminal in this folder, and run:

```powershell
python main.py
```

If Windows' `python` alias does not work, use `py main.py` or the full path to your
Python installation. On this computer the interpreter found during development is:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.15-64\python.exe" main.py
```

The app opens with the specified 20 ft W12x26 example. Edit inputs to recalculate,
or use the Calculate button, which stays visible above the scrolling panels.
Enter numbers in the units shown beside each field. All numeric inputs, including
I, S, E, and allowable bending stress, are directly editable; changing properties
automatically selects Custom. Choosing a catalog member restores its properties
and example material values.

Use **Spec examples** and **Load example** to start with any of the five cases in
`spec.md`, then edit any values. For example, case 2 loads a 10 ft simple beam with
one 20-kip point load at 5 ft and calculates a 50 kip-ft maximum moment. To enter
this case manually from Reset, remove the example's uniform load, change the span
to 10, add a point load with magnitude 20 and position 5, then Calculate.

Add/remove loads in the left panel. Both panels support two-finger trackpad
scrolling and mouse-wheel scrolling over fields, dropdowns, diagram canvases,
and scrollbars. Drag the divider to resize the panels. Reset example restores
the initial inputs. Cantilevers are fixed at the left.

Use **File → Save** or **Ctrl+S** to save the current beam as a `.beam.json` file;
**File → Open** or **Ctrl+O** restores it. Saved files include the support, span,
section and material selections and properties, the L/360 limit, and all loads.

After a valid calculation, choose **Export CSV** to save the sampled x, shear,
moment, and deflection values along the beam. The CSV includes units in its
column headings and opens in spreadsheet programs such as Excel.

Choose **Calculation Sheet PDF** after a valid calculation to create a report
with the beam inputs and loads first, followed by reactions, bending and
deflection checks, and the beam, shear, moment, and deflection diagrams.

The input panel has a minimum width so the divider cannot hide the form. After
updating the source, close existing Beam Designer windows and relaunch `main.py`;
already running Python processes continue using their previously loaded UI.

The input sections cover support type and span; point-load magnitude and position;
uniform-load magnitude, start, and end; steel/lumber member selection; and separate
I, S, E, and allowable bending stress entries. Loads may be combined and added,
edited, or removed. Partial uniform loads are supported within the span.

## Check calculations without opening a window

```powershell
python -m unittest discover -s tests -v
```

An optional integration check creates and destroys a hidden Tkinter window:

```powershell
python tests/ui_smoke.py
```

To check actual field visibility, click focus, keyboard entry, window resizing,
and automatic calculation of all five spec cases, run:

```powershell
python tests/ui_interaction.py
```

This briefly opens and closes a real test window. Unlike the hidden-window check,
it verifies that the displayed input panel has usable dimensions and that each
field is reachable by mouse. It also prevents a regression of the collapsed input
panel that earlier hidden-window checks missed.

The tests import only the calculation modules. `beam_designer.analysis.analyze`
accepts a `Beam` dataclass and returns a `Result`. It never imports Tkinter.
`BeamSolution` also exposes the continuous moment and deflection evaluators at
normalized position t=x/L for independent checks.

## Equations, signs, and catalog

The solver converts feet to inches and kip/ft to kip/in. Equilibrium determines
reactions, then singularity functions represent the piecewise bending moment.
Twice-integrated moment functions satisfy zero displacement at both simple
supports, or zero displacement and rotation at a cantilever's left fixed end.
Moment is positive in sagging (top in compression), shear is positive upward on
the left face, displacement is positive upward, and EI*y''=M. Fixed-end reaction
moment is positive counterclockwise; the corresponding internal moment is negative.
Endpoint loads are permitted, including loads directly carried by a support.

Moment and deflection extrema are found from polynomial roots in each load
interval, independently of the 400-interval drawing mesh. Root isolation uses
derivative roots and bounded bisection, so exact piecewise displacement equations
are evaluated with numerical root precision. Shear is evaluated on both sides of
point loads and supports. Bending stress converts kip-ft to kip-in before dividing
by S. Checks use unrounded values. Zero loads produce zero results.

Steel strong-axis properties come from the
[Nucor-Yamato structural shapes catalog](https://nucoryamato.com/staticdata/catalog.pdf):

| Member | I (in^4) | S (in^3) |
| --- | ---: | ---: |
| W12x26 | 204 | 33.4 |
| W12x22 | 156 | 25.4 |
| W12x19 | 130 | 21.3 |

Lumber sizes use rectangular geometry, I=b*d^3/12 and S=b*d^2/6: width 1.5 in,
depths 5.5, 7.25, 9.25, and 11.25 in for 2x6 through 2x12, oriented on edge.
Steel E=29,000 ksi and F_b=30 ksi, and lumber E=1,600 ksi and F_b=1 ksi are
explicit **example assumptions**, not grade-specific allowable design values.
Set appropriate material values for your analysis. This implements the specified
elastic bending and L/360 checks; it does not implement full code compliance,
buckling, shear strength, or the other checks excluded by `spec.md`.

With the W12x26 assumptions, the example has 10-kip reactions, 50 kip-ft maximum
moment, 0.609 in maximum deflection, 17.96 ksi bending stress, and 0.667 in limit.
Both checks pass.

For the required middle-half uniform load case, independent symmetric integration
gives M_max=3*w*L^2/32=37.5 kip-ft and
|delta_max|=57*w*L^4/(6144*E*I), at midspan. For the same W12x26 properties this is
0.434 in. This reference is recorded here and used in the calculation tests.

## Files

`models.py`, `catalog.py`, `validation.py`, and `analysis.py` contain data and
calculations. `ui.py` coordinates forms and results, while `diagrams.py` draws
Canvas diagrams and decorative shapes. The UI invalidates previous results
immediately when inputs change and recalculates after a short pause. Invalid or
missing fields display adjacent errors and suppress all calculated checks.

Development checks passed on Python 3.15.2 / Tk 9.0: 19 calculation/validation
tests and the hidden-window UI integration check. The UI check exercises startup,
invalid and incomplete inputs, Reset, add/remove loads, cantilever analysis,
material presets, custom properties, and Canvas redraws. Regression coverage also
enters values through input widgets, checks all five spec examples, and sends
small wheel deltas and Tk 9 TouchpadScroll events through both panels (including
dropdowns). The mapped-window interaction check passes at 1280x845 and 1040x700,
including keyboard entry of all five spec cases, invalid-load handling, and
automatic recalculation after correcting the input. Physical trackpad gestures
have not been tested on the user's device.
