"""Validation shared by the window and the window-free analysis API."""
from math import isfinite
from .models import PointLoad, UniformLoad, ValidationIssue


def finite(value):
    return isinstance(value, (int, float)) and isfinite(value)


def validate(beam):
    issues = []

    def issue(field, text):
        issues.append(ValidationIssue(field, text))

    valid_span = finite(beam.span) and beam.span > 0
    if not valid_span:
        issue("span", "Enter a finite span greater than zero.")
    if beam.support not in ("Simply supported", "Cantilever"):
        issue("support", "Choose a support type.")
    for name in ("inertia", "section_modulus", "elasticity", "allowable_stress"):
        value = getattr(beam.properties, name)
        if not finite(value) or value <= 0:
            issue(name, "Enter a finite value greater than zero.")
    for i, load in enumerate(beam.loads):
        prefix = f"loads.{i}."
        if not isinstance(load, (PointLoad, UniformLoad)):
            issue(prefix + "type", "Choose a point or uniform load.")
            continue
        if not finite(load.magnitude) or load.magnitude < 0:
            issue(prefix + "magnitude", "Enter a finite, nonnegative magnitude.")
        names = ("position",) if isinstance(load, PointLoad) else ("start", "end")
        for name in names:
            value = getattr(load, name)
            if not finite(value) or (valid_span and not 0 <= value <= beam.span):
                issue(prefix + name, "Enter a location from 0 to span.")
        if isinstance(load, UniformLoad) and finite(load.start) and finite(load.end):
            if load.start >= load.end:
                issue(prefix + "end", "End must be greater than start.")
    return issues
