from django.test import TestCase, override_settings
from django.urls import reverse


class ViewTests(TestCase):
    def test_index(self):
        response = self.client.get(reverse("trainhorn:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("trainhorn:spl"))
        self.assertContains(response, reverse("trainhorn:tank"))
        self.assertContains(response, reverse("trainhorn:wire"))
        self.assertTemplateUsed(response, "trainhorn/index.html")

    def test_urls_mounted_under_prefix(self):
        self.assertEqual(reverse("trainhorn:spl"), "/calc/spl/")

    def test_empty_forms_render(self):
        for name in ("spl", "tank", "wire"):
            response = self.client.get(reverse(f"trainhorn:{name}"))
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context["form"].is_bound)
            self.assertIsNone(response.context["result"])
            self.assertContains(response, '<html lang="en">')
            self.assertNotContains(response, "INVALID")

    def test_spl_result(self):
        response = self.client.get(reverse("trainhorn:spl"),
                                   {"source_db": "150", "ref_distance": "10", "distance": "100", "unit": "ft"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>130.0 dB</strong>", html=False)
        self.assertContains(response, 'role="status"')
        self.assertNotContains(response, "INVALID")

    def test_spl_form_errors(self):
        response = self.client.get(reverse("trainhorn:spl"), {"source_db": "150", "distance": "-1", "unit": "ft"})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["result"])
        form = response.context["form"]
        self.assertIn("distance", form.errors)
        self.assertIn("ref_distance", form.errors)
        self.assertContains(response, 'aria-invalid="true"')
        self.assertContains(response, "Enter a number greater than 0.")

    def test_tank_result_and_non_field_error(self):
        ok = self.client.get(reverse("trainhorn:tank"), {"tank_gallons": "5", "start_psi": "150",
                                                         "cutoff_psi": "110", "horn_cfm": "10", "blast_seconds": "2"})
        self.assertContains(ok, "<strong>10.9 s</strong>")
        self.assertContains(ok, "<strong>5</strong> blasts")
        bad = self.client.get(reverse("trainhorn:tank"), {"tank_gallons": "5", "start_psi": "100",
                                                          "cutoff_psi": "110", "horn_cfm": "10"})
        self.assertEqual(bad.status_code, 200)
        self.assertContains(bad, 'role="alert"')
        self.assertContains(bad, "must be greater than cutoff_psi")

    def test_wire_result(self):
        response = self.client.get(reverse("trainhorn:wire"), {"amps": "30", "one_way_length": "10", "unit": "ft",
                                                               "system_voltage": "12", "max_drop_pct": "3"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>6 AWG</strong>")

    def test_unrelated_query_params_do_not_bind(self):
        response = self.client.get(reverse("trainhorn:wire"), {"utm_source": "x"})
        self.assertFalse(response.context["form"].is_bound)

    @override_settings(TRAINHORN={"DECIMALS": 2})
    def test_decimals_setting(self):
        response = self.client.get(reverse("trainhorn:tank"), {"tank_gallons": "5", "start_psi": "150",
                                                               "cutoff_psi": "110", "horn_cfm": "10"})
        self.assertContains(response, "<strong>10.92 s</strong>")

    def test_labels_point_at_inputs(self):
        response = self.client.get(reverse("trainhorn:wire"))
        self.assertContains(response, '<label for="id_amps">')
        self.assertContains(response, 'id="id_amps"')
