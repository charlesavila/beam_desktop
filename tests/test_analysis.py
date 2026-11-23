"""Independent closed-form references; running these never opens Tkinter."""
import sys
import unittest
from dataclasses import replace
from beam_designer.analysis import analyze, BeamSolution, polynomial_roots
from beam_designer.catalog import example_beam
from beam_designer.models import Beam, PointLoad, UniformLoad


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.example = example_beam()
        self.props = self.example.properties
        self.ei = self.props.elasticity*self.props.inertia

    def beam(self, support, loads, span=10):
        return Beam(span, support, self.props, tuple(loads))

    def test_no_window_dependency(self):
        analyze(self.example)
        self.assertNotIn('tkinter', sys.modules)

    def test_required_example(self):
        r = analyze(self.example)
        self.assertAlmostEqual(r.left_reaction, 10)
        self.assertAlmostEqual(r.right_reaction, 10)
        self.assertAlmostEqual(r.governing_moment.value, 50)
        self.assertEqual(f'{abs(r.max_deflection.value):.3f}', '0.609')
        self.assertAlmostEqual(r.max_deflection.value, -5*(1/12)*240**4/(384*self.ei))
        self.assertAlmostEqual(r.deflection_limit, 2/3)
        self.assertAlmostEqual(r.stress, 600/33.4)
        self.assertTrue(r.bending_pass)
        self.assertTrue(r.deflection_pass)

    def test_center_point(self):
        r = analyze(self.beam('Simply supported', [PointLoad(20, 5)]))
        self.assertAlmostEqual(r.governing_moment.value, 50)
        self.assertAlmostEqual(r.max_deflection.value, -20*120**3/(48*self.ei))
        self.assertAlmostEqual(r.max_deflection.location, 5)

    def test_cantilever_tip(self):
        r = analyze(self.beam('Cantilever', [PointLoad(10, 10)]))
        self.assertAlmostEqual(r.left_reaction, 10)
        self.assertAlmostEqual(r.fixed_moment, 100)
        self.assertAlmostEqual(r.min_moment.value, -100)
        self.assertAlmostEqual(r.governing_moment.location, 0)
        self.assertAlmostEqual(r.max_deflection.value, -10*120**3/(3*self.ei))

    def test_cantilever_uniform(self):
        r = analyze(self.beam('Cantilever', [UniformLoad(1, 0, 10)]))
        self.assertAlmostEqual(r.left_reaction, 10)
        self.assertAlmostEqual(r.fixed_moment, 50)
        self.assertAlmostEqual(r.governing_moment.location, 0)
        self.assertAlmostEqual(r.max_deflection.value, -(1/12)*120**4/(8*self.ei))

    def test_middle_half_uniform(self):
        # Integration on the left half gives delta_mid=57*w*L^4/(6144*EI).
        r = analyze(self.beam('Simply supported', [UniformLoad(1, 5, 15)], 20))
        self.assertAlmostEqual(r.left_reaction, 5)
        self.assertAlmostEqual(r.right_reaction, 5)
        self.assertAlmostEqual(r.governing_moment.value, 37.5)
        self.assertAlmostEqual(r.max_deflection.value, -57*(1/12)*240**4/(6144*self.ei))
        self.assertAlmostEqual(r.max_deflection.location, 10)

    def test_zero_loads(self):
        for support in ('Simply supported', 'Cantilever'):
            r = analyze(self.beam(support, []))
            self.assertEqual(r.max_shear.value, 0)
            self.assertEqual(r.governing_moment.value, 0)
            self.assertEqual(r.max_deflection.value, 0)

    def test_loads_directly_at_supports(self):
        for support in ('Simply supported', 'Cantilever'):
            loads = [PointLoad(8, 0)]
            if support == 'Simply supported':
                loads.append(PointLoad(3, 10))
            r = analyze(self.beam(support, loads))
            self.assertEqual(r.left_reaction, 8)
            self.assertAlmostEqual(r.max_shear.value, 0)
            self.assertAlmostEqual(r.governing_moment.value, 0)
            self.assertAlmostEqual(r.max_deflection.value, 0)

    def test_combined_load_superposition(self):
        for support in ('Simply supported', 'Cantilever'):
            a = self.beam(support, [PointLoad(7, 3.1)])
            b = self.beam(support, [UniformLoad(0.7, 2, 9)])
            both = replace(a, loads=a.loads+b.loads)
            sa, sb, sc = [BeamSolution(v) for v in (a, b, both)]
            for i in range(101):
                t = i/100
                self.assertAlmostEqual(sc.moment(t), sa.moment(t)+sb.moment(t))
                self.assertAlmostEqual(sc.deflection(t), sa.deflection(t)+sb.deflection(t))
            self.assertAlmostEqual(sc.deflection(0), 0)
            if support == 'Simply supported':
                self.assertAlmostEqual(sc.deflection(1), 0)
            else:
                self.assertEqual(sc.c1, 0)
                self.assertAlmostEqual(sc.moment(1), 0)

    def test_off_center_extremum(self):
        # Point at a<L/2: x_max = L - sqrt((L^2-a^2)/3).
        r = analyze(self.beam('Simply supported', [PointLoad(10, 3)]))
        expected = 10-((100-9)/3)**0.5
        self.assertAlmostEqual(r.max_deflection.location, expected)
        self.assertAlmostEqual(r.governing_moment.value, 21)

    def test_shear_jump(self):
        s = BeamSolution(self.beam('Simply supported', [PointLoad(20, 5)]))
        self.assertEqual(s.shear(0.5, 'left'), 10)
        self.assertEqual(s.shear(0.5, 'right'), -10)

    def test_failure_checks_and_scaling(self):
        r = analyze(replace(self.example, loads=(UniformLoad(10, 0, 20),)))
        self.assertFalse(r.bending_pass)
        self.assertFalse(r.deflection_pass)
        self.assertAlmostEqual(r.governing_moment.value, 500)

    def test_extrema_between_plot_samples(self):
        r = analyze(self.beam('Simply supported', [UniformLoad(0.8, 0.7, 7.3), PointLoad(3, 9)]))
        s = BeamSolution(self.beam('Simply supported', [UniformLoad(0.8, 0.7, 7.3), PointLoad(3, 9)]))
        t = r.max_deflection.location/10
        self.assertAlmostEqual(s.integrated(t, 1)+s.c1, 0, places=6)

    def test_polynomial_repeated_roots(self):
        roots = polynomial_roots([-0.125, 0.75, -1.5, 1], 0, 1)
        self.assertTrue(any(abs(x-0.5) < 1e-7 for x in roots))


if __name__ == '__main__':
    unittest.main()
