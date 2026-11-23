from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PointLoad:
    magnitude: float
    position: float


@dataclass(frozen=True)
class UniformLoad:
    magnitude: float
    start: float
    end: float


@dataclass(frozen=True)
class Properties:
    inertia: float
    section_modulus: float
    elasticity: float
    allowable_stress: float


@dataclass(frozen=True)
class Beam:
    span: float
    support: str
    properties: Properties
    loads: Tuple = ()


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str


@dataclass(frozen=True)
class Extreme:
    value: float
    location: float


@dataclass(frozen=True)
class Sample:
    x: float
    shear: float
    moment: float
    deflection: float


@dataclass(frozen=True)
class Result:
    left_reaction: float
    right_reaction: float
    fixed_moment: float
    max_shear: Extreme
    max_moment: Extreme
    min_moment: Extreme
    governing_moment: Extreme
    max_deflection: Extreme
    stress: float
    deflection_limit: float
    bending_pass: bool
    deflection_pass: bool
    samples: Tuple[Sample, ...]
