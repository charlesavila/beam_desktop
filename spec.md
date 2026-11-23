# Beam Designer

## Purpose

Build a self-contained desktop application that analyzes a statically determinate beam and displays its shear, moment, and deflection diagrams. The application will accept common support conditions and load types, calculate the governing results, and indicate whether the selected beam is adequate for bending strength and L/360 deflection.

## Scope

- Deliver the application as a desktop program that runs on the user's computer.
- The application performs its analysis locally. It requires no server, account, external library, build step for end users, or network access.
- Beam and material properties may use static data embedded in the application.
- The interface is designed for a resizable desktop window.

## Assumptions and Units

- Analyze an idealized, prismatic beam using linear-elastic Euler-Bernoulli beam theory.
- Ignore shear deformation, axial deformation, beam self-weight, and second-order effects.
- Vertical loads act in the global downward direction. A downward load is positive in magnitude and produces the application's established sign conventions.
- Use the following internal signs:
  - Positive shear acts upward on the left face of a cut.
  - Positive moment causes compression on the top of the beam.
- Use feet for span and load locations.
- Use kips for point loads and kip/ft for distributed loads.
- Use inches for deflection and section dimensions.
- Use kip-ft for moments, kips for reactions and shear, ksi for stress and modulus of elasticity, in^3 for section modulus, and in^4 for moment of inertia.
- Display feet and kips with two decimal places, kip-ft with two decimal places, inches with three decimal places, and stress values with two decimal places.

## Inputs

### Beam and supports

- Support type:
  - Simply supported
  - Cantilever
- Span: a positive value in feet.

### Loads

- Add, edit, and remove an unlimited reasonable number of loads.
- Point load:
  - Magnitude in kips
  - Position from the left end in feet
- Uniformly distributed load:
  - Magnitude in kip/ft
  - Start location in feet
  - End location in feet
- Allow only downward loads in this initial version.
- Partial uniform loads are allowed anywhere within the span.

### Beam and material

- Supply the beam as either a steel W-shape or lumber size selected from a built-in catalog.
- A selected member must provide:
  - Moment of inertia about the bending axis, I
  - Elastic section modulus, S
- The material must provide:
  - Modulus of elasticity, E
  - Allowable bending stress, F_b
- The application may allow direct entry of I and S when a catalog member cannot represent the beam. If offered, require E and F_b as separate material inputs.

## Calculations

### Statics

- Calculate support reactions from vertical force and moment equilibrium.
- For a simply supported beam:
  - Calculate left and right vertical reactions.
- For a cantilever:
  - Calculate the fixed-end vertical reaction and fixed-end moment.
- Include all load effects in combined shear and moment calculations.

### Shear and moment

- Sample and evaluate shear and moment at each load boundary and support, and at enough intermediate points to represent linear shear and moment changes.
- Calculate the maximum absolute shear and maximum positive and negative moment.
- Show key shear and moment values on the diagrams.
- Preserve the sign convention defined above.

### Deflection

- Calculate beam deflection using E and I in consistent units.
- Include every point load and uniformly distributed load.
- Report the maximum absolute deflection and the location of maximum deflection.
- Include zero deflection at simple supports and at the cantilever fixed support.
- Use an exact solution appropriate to each load type and support condition.

### Bending check

- Calculate bending stress as:
  - f_b = |M_max| / S
- Compare it with the selected member's allowable bending stress:
  - Pass when f_b <= F_b
  - Fail when f_b > F_b
- Report both calculated stress and allowable stress.

### Deflection check

- Use the following limit:
  - Limit = span length / 360
- Compare the maximum absolute deflection with the limit:
  - Pass when |deflection_max| <= L/360
  - Fail when |deflection_max| > L/360
- Report both maximum deflection and the deflection limit.

## Outputs

### Beam diagram

- Show the span, support symbols, and each point or distributed load.
- Label load magnitudes and locations.
- Mark support reactions and their values after calculation.
- Draw a clear fixed support for a cantilever and pinned/roller supports for a simple beam.

### Diagrams

- Display separate shear, moment, and deflection diagrams in the desktop window, beneath or beside the beam diagram.
- Label each diagram, vertical axis, units, zero line, and key maximum or minimum values.
- Draw the shear line, moment curve, and deflection curve at scales that clearly represent the sign and shape.
- Use a consistent horizontal scale based on beam span.
- Provide a text summary of governing values so diagrams are not the only way to obtain results.

### Result summary

- Show reactions or fixed-end forces.
- Show maximum shear, maximum moment and location, maximum deflection and location, bending stress, allowable stress, and deflection limit.
- Separate bending and deflection checks.
- Use text and a distinct icon or symbol in addition to color for pass/fail states:
  - PASS
  - FAIL
  - INCOMPLETE or INVALID where required inputs are missing or invalid

## Interaction

- Open the desktop application with a complete example beam loaded:
  - 20 ft simply supported span
  - W12x26
  - Uniform load of 1 kip/ft
- Recalculate automatically after a valid input change.
- Do not show a misleading calculated or pass/fail result while inputs are incomplete or invalid.
- Provide an explicit **Calculate** action in addition to automatic recalculation.
- Provide **Reset** to restore the example beam.
- Provide controls to add and remove point and uniform loads.
- Provide an **Export CSV** action that saves the calculated x, shear V, moment M, and deflection values along the beam in a spreadsheet-compatible CSV file.
- Provide a **Calculation Sheet PDF** action that saves the inputs, diagrams, results, and bending/deflection checks in a report suitable for hand-in.
- Provide a File menu with Save and Open actions. Save and restore the support type, span, section and material selections and properties, the L/360 deflection limit, and all point and uniform loads.
- Update diagrams and the result summary together so no stale result remains visible.

## Validation Rules

- Reject an empty or non-numeric span.
- Require span to be greater than zero.
- Require point-load magnitude and location.
- Require point-load locations to be between 0 and span, inclusive.
- Require magnitude and start/end locations for distributed loads.
- Require distributed-load start and end values to be within the span and start < end.
- Permit a load to end at a support location.
- Reject negative magnitudes for point and distributed loads.
- Require selection of a beam and material or valid direct-entry beam properties.
- Require E, I, S, and F_b to be positive.
- Mark individual invalid fields visibly and provide concise adjacent error text.
- Prevent calculations and pass/fail checks when validation fails.
- Round display values only after calculations and comparisons are complete.

## Look and Feel

- Use a fun hippy type style with lots of abstract shapes and flowers and rainbows.
- Aim to give it a psychedelic feel, with lots of bright contrasting colors and swirls.
- Keep controls, diagrams, and results readable within a desktop application window.

## Additional Features
1. Save and Open: A File menu with Save and Open that saves the beam (support type, span, section, deflection limit, and loads) to a file and opens it again.
2. Export results: A button that saves a table of x, V, M, and deflection along the beam to a CSV file that opens in Excel.
3. Calculation sheet: A button that saves the diagrams and checks as a PDF, with the inputs listed at the top, ready to hand in with a design.

## Validation and Test Cases

The implementation must include at least the following hand-calculation cases:

1. **20 ft simple beam with 1 kip/ft**
   - W12x26
   - Reactions: 10 kips at each support
   - Maximum moment: 50.0 kip-ft
   - Maximum deflection: 0.609 in
   - Deflection limit: 20 ft / 360 = 0.667 in

2. **10 ft simple beam with a 20 kip center point load**
   - Maximum moment: 50.0 kip-ft
   - Maximum deflection: P L^3 / (48 E I) using the selected member properties

3. **10 ft cantilever with a 10 kip end point load**
   - Fixed reaction: 10 kips
   - Fixed-end moment: 100 kip-ft
   - Maximum moment location: fixed support

4. **10 ft cantilever with 1 kip/ft uniform load**
   - Fixed reaction: 10 kips
   - Fixed-end moment: 50 kip-ft
   - Maximum moment location: fixed support

5. **20 ft simple beam with a 1 kip/ft uniform load over the middle 10 ft**
   - Symmetric reactions: 5 kips each
   - Maximum moment: hand-check against statics and a standard partial-distributed-load solution
   - Maximum deflection: hand-calculated and recorded before implementation

Additional required cases:

- Zero loads: reactions, shear, moment, and deflection must be zero.
- Invalid span: no calculation is shown and a visible validation error appears.
- Load outside the span: no calculation is shown and a visible validation error appears.
- Invalid distributed load range: no calculation is shown and a visible validation error appears.
- Missing member property: no pass/fail result is shown.

## Acceptance Criteria

- The desktop application opens with the valid example beam and displays complete results.
- Every required input has a label and validation behavior.
- All supported input combinations produce reactions, shear, moment, deflection, and pass/fail results without stale values.
- Simply supported and cantilever cases use the correct boundary conditions.
- Partial distributed loads and point loads can be combined in one analysis.
- The unit tests or hand calculations above agree within the displayed rounding.
- Invalid inputs never produce a valid-looking pass/fail result.
- Reset restores the original example beam.
- Add and remove load controls work for point and distributed loads.
- The beam and three diagrams remain readable at supported desktop window sizes.
- The application requires no external assets or network access.
- No feature outside this spec is required.

## Out of Scope

- Continuous beams
- Indeterminate beams
- Buckling and lateral-torsional stability
- Combined axial and bending checks
- Column or connection design
- Dynamic, seismic, or moving loads
- Plate, finite-element, or 3D analysis
- Fabrication, cost, or detailed code compliance
