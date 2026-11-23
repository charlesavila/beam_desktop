import math
import unittest
from dataclasses import replace
from beam_designer.catalog import example_beam
from beam_designer.models import PointLoad, UniformLoad
from beam_designer.validation import validate
from beam_designer.analysis import analyze


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.beam = example_beam()

    def test_invalid_spans(self):
        for span in (0, -1, math.nan, math.inf, None, ''):
            b = replace(self.beam, span=span)
            self.assertTrue(validate(b))
            with self.assertRaises(ValueError):
                analyze(b)

    def test_invalid_loads(self):
        for load in (PointLoad(-1, 5), PointLoad(1, 21), PointLoad(1, -1),
                     PointLoad(math.inf, 1), PointLoad(1, math.nan),
                     UniformLoad(1, 4, 4), UniformLoad(1, 8, 4),
                     UniformLoad(1, 0, 21), UniformLoad(-1, 0, 20)):
            self.assertTrue(validate(replace(self.beam, loads=(load,))))

    def test_invalid_properties(self):
        for field in ('inertia', 'section_modulus', 'elasticity', 'allowable_stress'):
            for value in (0, -1, math.nan, math.inf, None):
                props = replace(self.beam.properties, **{field: value})
                self.assertTrue(validate(replace(self.beam, properties=props)))

    def test_valid_boundaries_and_zero_load(self):
        b = replace(self.beam, loads=(PointLoad(0, 0), PointLoad(1, 20), UniformLoad(0, 0, 20)))
        self.assertFalse(validate(b))

    def test_invalid_support(self):
        self.assertTrue(validate(replace(self.beam, support='Continuous')))


if __name__ == '__main__':
    unittest.main()
