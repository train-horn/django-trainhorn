"""The vendored core must match trainhorn-calc 1.0.0 reference vectors."""

import math

from django.test import SimpleTestCase

from trainhorn import calc
from trainhorn.calc import InputError


class ParityTests(SimpleTestCase):
    def test_150db_at_10ft_gives_130_at_100ft(self):
        self.assertAlmostEqual(calc.spl_at_distance(150, 100), 130.0, places=9)
        self.assertAlmostEqual(calc.spl_at_distance(150, 100, ref_distance=10, unit="ft"), 130.0, places=9)

    def test_spl_reference_vectors(self):
        self.assertAlmostEqual(calc.spl_at_distance(118, 10), 118.0)
        self.assertAlmostEqual(calc.spl_at_distance(150, 5), 150 + 20 * math.log10(2))
        self.assertAlmostEqual(calc.spl_at_distance(120, 10, ref_distance=1, unit="m"), 100.0)

    def test_distance_for_spl_vectors(self):
        self.assertAlmostEqual(calc.distance_for_spl(150, 130), 100.0, places=9)
        self.assertAlmostEqual(calc.distance_for_spl(150, 90), 10000.0, places=6)

    def test_doubling_and_combination(self):
        self.assertAlmostEqual(calc.db_doubling_loss(), 6.0206, places=4)
        self.assertAlmostEqual(calc.combine_levels([100, 100]), 100 + 10 * math.log10(2))

    def test_air_system_vectors(self):
        self.assertAlmostEqual(calc.tank_runtime_seconds(5, 150, 110, 10), 10.91566866267465)
        self.assertEqual(calc.blast_count(calc.tank_runtime_seconds(5, 150, 110, 10), 2), 5)
        self.assertAlmostEqual(calc.compressor_recovery_seconds(2, 110, 150, 1.0), 43.662674650698605)
        self.assertAlmostEqual(calc.free_air_volume_cuft(1, 14.696, 0), 231 / 1728)

    def test_wire_vectors(self):
        self.assertEqual(calc.suggest_awg(30, 10).awg, "6")
        # Same published solid-copper table (ohm / 1000 ft at 20 C) and 1 % tolerance as upstream.
        published = {"14": 2.525, "12": 1.588, "10": 0.9989, "8": 0.6282, "4": 0.2485, "1/0": 0.09827}
        for gauge, ohms in published.items():
            self.assertAlmostEqual(calc.awg_resistance_ohm_per_1000ft(gauge), ohms, delta=ohms * 0.01)

    def test_input_error_is_value_error(self):
        self.assertTrue(issubclass(InputError, ValueError))
        with self.assertRaises(InputError):
            calc.tank_runtime_seconds(5, 100, 110, 10)

    def test_core_version(self):
        self.assertEqual(calc.CORE_VERSION, "1.0.0")
