# Prompt log

## 2026-11-23

- **Asked:** Add a calculation sheet button that saves the diagrams and checks as a PDF, with inputs listed at the top, ready to hand in with a design.
- **Changed:** Added a dependency-free PDF calculation sheet exporter and toolbar button. The report starts with support, span, section/material properties, deflection limit, loads, reactions, and PASS/FAIL checks, then includes vector beam, shear, moment, and deflection diagrams. Long load lists continue on additional pages. Added the feature to the spec and README.
- **Worked:** Implementation complete. Not run or manually inspected.

## 2026-11-23

- **Asked:** Add a button that exports a table of x, shear V, moment M, and deflection along the beam to a CSV file that opens in Excel.
- **Changed:** Added an Export CSV toolbar button that exports the current valid analysis samples with unit-labeled headers, using Excel-friendly UTF-8 encoding. It asks for a valid calculation first and reports write errors. Added the feature to the spec and README.
- **Worked:** Implementation complete. Not run or manually exercised.

## 2026-11-23

- **Asked:** Add a File menu with Save and Open for beam designs, saving support type, span, section, deflection limit, and loads; remove “Saving designs” from the spec's Out of scope section first.
- **Changed:** Added Save/Open menu actions and Ctrl+S/Ctrl+O shortcuts. Versioned `.beam.json` files preserve support, span, section/material selections and properties, the L/360 limit, and all point/uniform loads; opening restores inputs and recalculates. Added the feature to the spec's Interaction section and documented the workflow in README. The spec's Out of Scope section did not contain a “Saving designs” item.
- **Worked:** Implementation complete. Not run or manually exercised.

## 2026-11-23

- **Asked:** Read `spec.md` and, before writing code, describe a plan for building the Python Tkinter desktop app, including files, calculation organization, potential issues, and suggested fixes; put the plan in `plan.md`.
- **Changed:** Added the implementation plan to `plan.md`, including proposed modules, unit and analysis flow, UI structure, risks, and refinements. No application code was written.
- **Worked:** Yes. The plan was saved. `spec.md` describes a desktop app but does not itself name Tkinter; the plan records Tkinter as the framework specified in the request.

## 2026-11-23

- **Asked:** Does the code keep beam calculations apart from the window code so they can be checked without opening the app?
- **Changed:** No application code exists yet. The plan already separates calculations into `beam_designer/analysis.py` and proposes tests that do not import or open the Tkinter UI.
- **Worked:** Clarified that this is planned architecture, not implemented behavior.

## 2026-11-23

- **Asked:** Build the app based on the plan.
- **Changed:** Created the Python Tkinter desktop application with separate data, catalog, validation, calculation, UI, and Canvas drawing modules. Added automatic recalculation, load editing, Reset, member/material selection and custom properties, support reactions, three diagrams, and separate bending/deflection checks. Added calculation tests, a hidden-window UI integration check, README launch instructions and documented assumptions, and updated the plan's implementation status.
- **Worked:** Yes. All 19 calculation/validation tests passed on Python 3.15.2. The Tk 9.0 hidden-window integration check passed for startup, validation, stale-result clearing, reset, load editing, materials, custom properties, and diagram redraws. The W12x26 example reproduces 10-kip reactions, 50 kip-ft moment, and 0.609 in deflection. No manual visual review was performed.

## 2026-11-23

- **Asked:** Allow entering the values from `spec.md` and calculating results; fix trackpad scrolling.
- **Changed:** Added Tk 9 TouchpadScroll support, retained fractional mouse-wheel movements, and routed scrolling over child widgets to their containing panel without changing dropdown selections. Moved Calculate and Reset to a fixed toolbar. Made I and S directly editable alongside all other numeric inputs, with automatic Custom selection when properties change. Added all five spec cases as editable starting examples and documented manual input steps. Extended UI regression checks for spec examples, typed inputs, direct property editing, and scrolling events.
- **Worked:** The hidden-window regression check passed with all five spec cases, manual entry of the 10 ft center-point-load case, custom properties, and simulated small wheel/trackpad events in both panels. Physical trackpad behavior has not been tested on the user's device.

## 2026-11-23

- **Asked:** Read `spec.md`, implement its requirements, and focus on the Inputs through Calculations sections because the app still does not allow input.
- **Changed:** Reproduced the actual first-launch failure in a mapped window: the input canvas viewport could be only one pixel wide because the initial sash position was set before window allocation. Replaced that initialization with a pane layout that enforces minimum input and output widths. Reviewed the spec's support, span, loads, catalogs, direct property input, and calculation requirements against the existing implementation. Added `tests/ui_interaction.py` to check visible layout, mouse targeting, actual keyboard bindings, minimum-size resizing, divider limits, and manual entry/automatic calculation of all five spec cases. Updated README and plan with the fix and the stronger regression check.
- **Worked:** Yes. The mapped-window regression passed at 1280x845 and 1040x700: every numeric field was reachable and accepted keyboard input, all five spec cases produced the expected governing moments, and invalid loads cleared results until corrected. All 19 calculation/validation tests passed. Existing app windows must be closed and reopened to load the updated code.

## 2026-11-23

- **Asked:** Why is there a `.gitignore` file?
- **Changed:** Explained that it excludes generated Python cache folders and compiled files from Git tracking. Logged this explanation; no application files changed.
- **Worked:** Yes. Confirmed the file contains `__pycache__/` and `*.py[cod]`.
