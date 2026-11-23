# Beam Designer implementation plan

## Platform and scope

Implement the application in Python with Tkinter and the Python standard library. The current `spec.md` defines a desktop application but does not name Tkinter; Tkinter is the framework specified in the request. Keep the analysis local and avoid runtime downloads, external packages, and a server.

The first implementation should cover the stated simply supported and cantilever cases, downward point loads and partial or full uniform loads, the required member/material inputs, the three diagrams, validation, and result checks. Do not add features from the out-of-scope list.

## Proposed files

- `main.py` — application entry point; creates the Tk root window and starts the UI.
- `beam_designer/__init__.py` — marks the application package and exposes no UI behavior.
- `beam_designer/models.py` — dataclasses for beam configuration, supports, point loads, uniform loads, section/material properties, validation issues, and calculated results.
- `beam_designer/catalog.py` — built-in section and material records, including the W12x26 example; keeps catalog values and their units in one place.
- `beam_designer/validation.py` — checks required values, positive properties, load ranges, and support-specific input constraints; returns field-addressable messages for the UI.
- `beam_designer/analysis.py` — unit conversion, equilibrium reactions, shear and moment functions, exact elastic deflection, extrema, and bending/deflection checks. This module should not import Tkinter.
- `beam_designer/diagrams.py` — draws the beam, loads, reactions, shear, moment, and deflection on resizable Tkinter Canvas widgets from calculated result data.
- `beam_designer/ui.py` — Tkinter window, input forms, load editing controls, validation display, Calculate/Reset actions, result summary, and automatic recalculation coordination.
- `tests/test_analysis.py` — standard-library `unittest` cases for hand calculations, sign conventions, boundary conditions, combinations of loads, and extrema.
- `tests/test_validation.py` — standard-library `unittest` cases for invalid and boundary input values.
- `README.md` — how to launch the app, run its tests, and understand the built-in catalog values.

## Calculation organization

1. **Represent inputs in model objects.** Keep entered lengths in feet, loads in kips or kip/ft, section dimensions in inches, E in ksi, and I/S in their specified inch units. Preserve unrounded values internally.
2. **Validate before analysis.** The UI asks the validation module for field errors. If any input is incomplete or invalid, clear or mark calculated output as invalid and do not show pass/fail results.
3. **Convert once at the analysis boundary.** Convert span and positions to inches and uniform loads to kip/in, so all deflection equations use compatible units with E in kip/in² and I in in⁴. Keep report values converted to the spec's display units.
4. **Solve reactions using equilibrium.** Sum point loads and each uniform load's resultant and centroid. Solve left/right reactions for a simple beam; solve vertical reaction and fixed-end moment for a cantilever.
5. **Build piecewise internal-force expressions.** Add reaction and load contributions using a consistent coordinate from the left end. Treat each uniform load as a start contribution and an end contribution so partial loads combine cleanly. Define and document the signs against the spec's positive shear and positive moment descriptions.
6. **Compute deflection by elastic superposition.** Integrate the piecewise moment/load expressions with integration constants chosen to satisfy support boundary conditions: zero displacement at both simple supports; zero displacement and rotation at the cantilever fixed end. Use the same load contributions for mixed point and uniform loading, and keep the deflection sign mapping explicit.
7. **Find governing values before rounding.** Evaluate breakpoints at supports and load boundaries plus interior extrema (for example, shear zeros for moment extrema and slope zeros for deflection extrema). Retain coordinates and full precision for checks; round only when formatting display text.
8. **Return a calculation result object.** Include reactions, diagram sample coordinates and values, maxima/minima with locations, bending stress, L/360 limit, and separate bending and deflection statuses. The UI updates all diagrams and summaries from this one result to avoid stale outputs.

## UI organization

Use `ttk` forms for support, span, member/material, and load entry; a row-based editor should allow adding/removing point and uniform loads. Use a resizable `ttk.Panedwindow` or equivalent layout for inputs and results, with scrollable input/results areas if needed. Draw diagrams on `Canvas` so the application needs no plotting package. Redraw all diagrams when a new valid result is produced or the window changes size. Include clear text labels and pass/fail symbols in addition to colors. Reset restores the stated 20 ft simply supported W12x26 example with a 1 kip/ft full-span load.

## Potential issues and proposed refinements

- **Catalog data is underspecified.** The spec requires steel W-shapes and lumber sizes but does not list catalog members, E, S, I, or allowable stresses. Start with the required W12x26 example and a small explicitly documented built-in set, and provide direct property entry for other sections. Record data sources and units in `catalog.py`/README; do not imply comprehensive code design coverage.
- **Example deflection depends on properties.** The specified 0.609 in value for the 20 ft example depends on E and I, neither of which is given in the spec. Confirm the intended W12x26 values and material assumptions, or adjust the expected example result once those values are established. Do not hard-code the target deflection independently of the chosen catalog data.
- **The moment sign wording needs a precise equation convention.** “Positive moment causes compression on the top” should be mapped to the internal cut convention and the curvature/deflection equation in one place, then locked down with cantilever and simple-beam tests. Typical engineering plotting conventions differ, so diagram labels and signs must follow the spec consistently.
- **Deflection “exact solution” needs a method for arbitrary load combinations.** Use piecewise/singularity-function integration and superposition with boundary conditions, then locate extrema analytically or with a bounded numerical root method on each interval. A fixed coarse sampling grid alone can miss the true maximum and is not enough for the stated exact-solution requirement.
- **Loads at supports and cantilever endpoints need defined behavior.** The spec permits point loads at either end of the span, where a simple-support load may be directly carried by a reaction and a cantilever load at its fixed end may have a special effect. Define these boundary cases and test them, or disallow only cases that are mechanically ambiguous and update the spec accordingly.
- **A uniform load ending at a support is explicitly allowed.** Include the endpoint without introducing an artificial discontinuity in the integrated result; test full-span and partial-span loads, including both support boundaries.
- **Tkinter has no built-in graphing or modern responsive layout.** Canvas drawing and a deliberately simple resizable layout meet the no-external-assets requirement, but small windows can become crowded. Set a reasonable minimum window size and verify diagrams, error text, and controls remain accessible at supported desktop sizes.
- **Automatic recalculation must not show stale results.** Debounce text-entry changes if necessary, validate complete input snapshots, and clear prior results immediately when the current inputs become invalid.

## Implementation sequence

1. Implement models, catalog data, unit conversions, validation, and calculation functions.
2. Establish calculation behavior and sign conventions with unit tests for the required cases, including zero load, partial load, endpoint cases, and mixed loads.
3. Build the Tkinter form and load editor, wiring validation, Calculate, Reset, and valid-change recalculation to the calculation module.
4. Add canvas beam/force/deflection diagrams and resize-aware redraw behavior.
5. Check the complete app against every acceptance criterion and document launch/test commands and catalog assumptions.

## Implementation status

Implemented the Python Tkinter desktop application and the files described above.
The calculation modules do not import Tkinter. The W12x26 example uses I=204 in^4,
S=33.4 in^3, and E=29,000 ksi, reproducing the specified 0.609 in deflection.
Catalog/material assumptions and the partial-uniform-load reference are recorded
in README.md. All 19 calculation/validation tests and the hidden-window Tkinter
integration check passed. Launch with `python main.py` (see README for the local
interpreter path if Windows' Python alias does not work).

The input-pane sizing was subsequently corrected to enforce a usable minimum
width from first launch. `tests/ui_interaction.py` now checks a real mapped window,
mouse targeting, keyboard entry into every numeric field, resizing, and automatic
calculation of all five spec cases; these checks catch layout failures that a
withdrawn-window test cannot detect.
