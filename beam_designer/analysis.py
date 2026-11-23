"""Exact elastic beam functions, independent of Tkinter.

Use t=x/L internally to improve polynomial conditioning. M is kip-in,
positive in sagging; V=dM/dx is positive upward on the left face.
Displacement is positive upward, so EI*y''=M and downward deflection is negative.
The cantilever is fixed at the left. Fixed reaction moment is positive CCW.
"""
from math import comb, factorial, isfinite
from .models import PointLoad, UniformLoad, Extreme, Sample, Result
from .validation import validate


def polynomial_roots(coefficients, low, high):
    """All real polynomial roots on a bounded interval via derivative isolation."""
    c = list(coefficients)
    while len(c) > 1 and c[-1] == 0:
        c.pop()
    if len(c) <= 1:
        return []
    scale = max(abs(v) for v in c)
    c = [v / scale for v in c]

    def evaluate(x):
        value = 0.0
        for a in reversed(c):
            value = value * x + a
        return value

    critical = polynomial_roots([i*c[i] for i in range(1, len(c))], low, high)
    bounds = [low] + critical + [high]
    roots = [x for x in bounds if abs(evaluate(x)) < 1e-13]
    for a, b in zip(bounds, bounds[1:]):
        fa, fb = evaluate(a), evaluate(b)
        if fa * fb >= 0:
            continue
        for _ in range(50):
            mid = (a+b)/2
            fm = evaluate(mid)
            if fa * fm <= 0:
                b = mid
            else:
                a, fa = mid, fm
        roots.append((a+b)/2)
    return sorted(set(roots))


class BeamSolution:
    """Validated beam with evaluators and exact polynomial segments."""

    def __init__(self, beam):
        issues = validate(beam)
        if issues:
            raise ValueError("; ".join(f"{i.field}: {i.message}" for i in issues))
        self.beam = beam
        self.length = beam.span * 12
        length = self.length
        total = sum(p.magnitude if isinstance(p, PointLoad) else
                    p.magnitude * (p.end-p.start) for p in beam.loads)
        moment = sum(p.magnitude*p.position if isinstance(p, PointLoad) else
                     p.magnitude*(p.end-p.start)*(p.start+p.end)/2 for p in beam.loads)
        self.right = moment/beam.span if beam.support == "Simply supported" else 0.0
        self.left = total-self.right
        self.fixed = moment if beam.support == "Cantilever" else 0.0
        self.terms = [(-self.fixed*12, 0.0, 0), (self.left*length, 0.0, 1)]
        boundaries = {0.0, 1.0}
        for p in beam.loads:
            if isinstance(p, PointLoad):
                a = p.position/beam.span
                self.terms.append((-p.magnitude*length, a, 1))
                boundaries.add(a)
            else:
                a, b = p.start/beam.span, p.end/beam.span
                coefficient = p.magnitude/12 * length**2 / 2
                self.terms.extend([(-coefficient, a, 2), (coefficient, b, 2)])
                boundaries.update((a, b))
        self.boundaries = sorted(boundaries)
        self.c1 = -self.integrated(1, 2) if beam.support == "Simply supported" else 0.0
        self.factor = length**2/(beam.properties.elasticity*beam.properties.inertia)
        if not all(isfinite(v) for v in (self.left, self.right, self.fixed, self.factor, self.c1)):
            raise ValueError("Values exceed the supported numerical range.")

    def integrated(self, t, order):
        return sum(c*max(t-a, 0)**(p+order)*factorial(p)/factorial(p+order)
                   for c, a, p in self.terms)

    def moment(self, t):
        return self.integrated(t, 0)/12

    def deflection(self, t):
        return self.factor * (self.integrated(t, 2) + self.c1*t)

    def shear(self, t, side="right"):
        if (t == 0 and side == "left") or (t == 1 and side == "right"):
            return 0.0
        value = self.left
        for load in self.beam.loads:
            if isinstance(load, PointLoad):
                a = load.position/self.beam.span
                if t > a or (t == a and side == "right"):
                    value -= load.magnitude
            else:
                x = t*self.beam.span
                value -= load.magnitude*max(0.0, min(x, load.end)-load.start)
        return value

    def segment_polynomial(self, low, order):
        """Coefficients of the order-th integral of M, in z=t-low."""
        coeff = [0.0]*(3+order)
        for c, a, p in self.terms:
            if a <= low:
                degree = p+order
                multiplier = c*factorial(p)/factorial(degree)
                for k in range(degree+1):
                    coeff[k] += multiplier*comb(degree, k)*(low-a)**(degree-k)
        if order == 1:
            coeff[0] += self.c1
        return coeff

    def result(self):
        moment_points = set(self.boundaries)
        deflection_points = set(self.boundaries)
        for low, high in zip(self.boundaries, self.boundaries[1:]):
            # Derivative of moment is linear within each interval.
            c = self.segment_polynomial(low, 0)
            moment_points.update(low+z for z in polynomial_roots(
                [i*c[i] for i in range(1, len(c))], 0, high-low))
            deflection_points.update(low+z for z in polynomial_roots(
                self.segment_polynomial(low, 1), 0, high-low))
        moments = [Extreme(self.moment(t), t*self.beam.span) for t in sorted(moment_points)]
        deflections = [Extreme(self.deflection(t), t*self.beam.span) for t in sorted(deflection_points)]
        shears = [Extreme(self.shear(t, side), t*self.beam.span)
                  for t in self.boundaries for side in ("left", "right")]
        governing = max(moments, key=lambda v: abs(v.value))
        displacement = max(deflections, key=lambda v: abs(v.value))
        stress = abs(governing.value)*12/self.beam.properties.section_modulus
        limit = self.length/360
        positions = set(i/400 for i in range(401)) | moment_points | deflection_points
        samples = []
        for t in sorted(positions):
            for side in (("left", "right") if t in self.boundaries else ("right",)):
                samples.append(Sample(t*self.beam.span, self.shear(t, side),
                                      self.moment(t), self.deflection(t)))
        values = [stress, limit] + [v for s in samples for v in (s.shear, s.moment, s.deflection)]
        if not all(isfinite(v) for v in values):
            raise ValueError("Values exceed the supported numerical range.")
        return Result(self.left, self.right, self.fixed,
                      max(shears, key=lambda v: abs(v.value)),
                      max(moments, key=lambda v: v.value), min(moments, key=lambda v: v.value),
                      governing, displacement, stress, limit,
                      stress <= self.beam.properties.allowable_stress,
                      abs(displacement.value) <= limit, tuple(samples))


def analyze(beam):
    """Return reactions, diagrams and checks without importing a window library."""
    return BeamSolution(beam).result()
