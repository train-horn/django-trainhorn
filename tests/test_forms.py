from django.test import SimpleTestCase, override_settings

from trainhorn.forms import SPLForm, TankRuntimeForm, WireGaugeForm


class SPLFormTests(SimpleTestCase):
    def test_valid(self):
        form = SPLForm({"source_db": "150", "ref_distance": "10", "distance": "100", "unit": "ft"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertAlmostEqual(form.result["level_db"], 130.0, places=9)
        self.assertIsNone(form.result["target_distance"])

    def test_valid_with_target_and_absorption(self):
        form = SPLForm({"source_db": "150", "ref_distance": "10", "distance": "100", "unit": "ft",
                        "target_db": "130", "absorption_db_per_km": "0"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertAlmostEqual(form.result["target_distance"], 100.0, places=6)

    def test_missing_and_bad_fields(self):
        form = SPLForm({"source_db": "abc", "ref_distance": "0", "unit": "yd"})
        self.assertFalse(form.is_valid())
        self.assertIn("source_db", form.errors)
        self.assertIn("ref_distance", form.errors)
        self.assertIn("distance", form.errors)
        self.assertIn("unit", form.errors)
        self.assertIsNone(form.result)

    def test_negative_distance(self):
        form = SPLForm({"source_db": "150", "ref_distance": "10", "distance": "-5", "unit": "ft"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["distance"], ["Enter a number greater than 0."])

    def test_errors_marked_for_screen_readers(self):
        form = SPLForm({"source_db": "150", "ref_distance": "10", "distance": "", "unit": "ft"})
        self.assertFalse(form.is_valid())
        html = str(form["distance"])
        self.assertIn('aria-invalid="true"', html)
        self.assertIn("id_distance_errors", html)

    @override_settings(TRAINHORN={"DEFAULT_UNIT": "m", "DEFAULT_REF_DISTANCE": 1})
    def test_initial_from_settings(self):
        form = SPLForm()
        self.assertEqual(form.fields["unit"].initial, "m")
        self.assertEqual(form.fields["ref_distance"].initial, 1)


class TankRuntimeFormTests(SimpleTestCase):
    def test_valid(self):
        form = TankRuntimeForm({"tank_gallons": "5", "start_psi": "150", "cutoff_psi": "110", "horn_cfm": "10",
                                "blast_seconds": "2", "compressor_cfm": "1"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertAlmostEqual(form.result["runtime_seconds"], 10.91566866267465)
        self.assertEqual(form.result["blasts"], 5)
        self.assertAlmostEqual(form.result["recovery_seconds"], 5 / 2 * 43.662674650698605)

    def test_optional_fields_empty(self):
        form = TankRuntimeForm({"tank_gallons": "5", "start_psi": "150", "cutoff_psi": "110", "horn_cfm": "10"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.result["blasts"])
        self.assertIsNone(form.result["recovery_seconds"])

    def test_cutoff_above_start_is_non_field_error(self):
        form = TankRuntimeForm({"tank_gallons": "5", "start_psi": "100", "cutoff_psi": "110", "horn_cfm": "10"})
        self.assertFalse(form.is_valid())
        self.assertIn("must be greater than cutoff_psi", form.non_field_errors()[0])
        self.assertIsNone(form.result)

    def test_zero_tank(self):
        form = TankRuntimeForm({"tank_gallons": "0", "start_psi": "150", "cutoff_psi": "110", "horn_cfm": "10"})
        self.assertFalse(form.is_valid())
        self.assertIn("tank_gallons", form.errors)


class WireGaugeFormTests(SimpleTestCase):
    def test_valid(self):
        form = WireGaugeForm({"amps": "30", "one_way_length": "10", "unit": "ft", "system_voltage": "12",
                              "max_drop_pct": "3"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.result["awg"], "6")
        self.assertLessEqual(form.result["wire"].voltage_drop_pct, 3)

    def test_24v_needs_thinner_or_equal_wire(self):
        data = {"amps": "30", "one_way_length": "10", "unit": "ft", "max_drop_pct": "3"}
        f12 = WireGaugeForm(dict(data, system_voltage="12"))
        f24 = WireGaugeForm(dict(data, system_voltage="24"))
        self.assertTrue(f12.is_valid() and f24.is_valid())
        order = ["18", "16", "14", "12", "10", "8", "6", "4", "2", "1", "1/0", "2/0", "3/0", "4/0"]
        self.assertLessEqual(order.index(f24.result["awg"]), order.index(f12.result["awg"]))

    def test_impossible_run_is_non_field_error(self):
        form = WireGaugeForm({"amps": "5000", "one_way_length": "500", "unit": "ft", "system_voltage": "12",
                              "max_drop_pct": "3"})
        self.assertFalse(form.is_valid())
        self.assertIn("no gauge up to 4/0", form.non_field_errors()[0])

    def test_drop_over_50(self):
        form = WireGaugeForm({"amps": "30", "one_way_length": "10", "unit": "ft", "system_voltage": "12",
                              "max_drop_pct": "60"})
        self.assertFalse(form.is_valid())
        self.assertIn("max_drop_pct", form.errors)
