"""Strong-axis section properties; see README for sources and assumptions."""
from .models import Beam, PointLoad, Properties, UniformLoad

# Steel: Nucor-Yamato structural shapes catalog, Ix in in^4, Sx in in^3.
# Lumber: rectangular section formulas using dressed dimensions in inches.
SECTIONS = {
    "W12x26": (204.0, 33.4, "Steel (example)"),
    "W12x22": (156.0, 25.4, "Steel (example)"),
    "W12x19": (130.0, 21.3, "Steel (example)"),
}
for name, depth in (("2x6", 5.5), ("2x8", 7.25), ("2x10", 9.25), ("2x12", 11.25)):
    SECTIONS[f"Lumber {name}"] = (1.5 * depth**3 / 12, 1.5 * depth**2 / 6,
                                   "Lumber (example)")

# Illustrative editable material assumptions, not grade-specific design values.
MATERIALS = {"Steel (example)": (29000.0, 30.0),
             "Lumber (example)": (1600.0, 1.0)}


def example_beam():
    return Beam(20.0, "Simply supported", Properties(204, 33.4, 29000, 30),
                (UniformLoad(1, 0, 20),))


SPEC_EXAMPLES = {
    "1. Simple / 20 ft / 1 kip/ft": example_beam(),
    "2. Simple / 10 ft / 20 kip at center": Beam(
        10, "Simply supported", example_beam().properties, (PointLoad(20, 5),)),
    "3. Cantilever / 10 ft / 10 kip at end": Beam(
        10, "Cantilever", example_beam().properties, (PointLoad(10, 10),)),
    "4. Cantilever / 10 ft / 1 kip/ft": Beam(
        10, "Cantilever", example_beam().properties, (UniformLoad(1, 0, 10),)),
    "5. Simple / 20 ft / middle 10 ft loaded": Beam(
        20, "Simply supported", example_beam().properties, (UniformLoad(1, 5, 15),)),
}
