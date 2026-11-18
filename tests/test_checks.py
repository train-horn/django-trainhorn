from django.core import checks
from django.test import SimpleTestCase, override_settings

from trainhorn.checks import check_settings


def ids(messages):
    return sorted(m.id for m in messages)


class CheckTests(SimpleTestCase):
    def test_defaults_pass(self):
        self.assertEqual(check_settings(), [])

    def test_registered(self):
        self.assertEqual([m for m in checks.run_checks() if m.id.startswith("trainhorn.")], [])

    @override_settings(TRAINHORN=["ft"])
    def test_not_a_dict(self):
        self.assertEqual(ids(check_settings()), ["trainhorn.E001"])

    @override_settings(TRAINHORN={"DEFAULT_UNIT": "yd"})
    def test_bad_unit(self):
        self.assertEqual(ids(check_settings()), ["trainhorn.E002"])

    @override_settings(TRAINHORN={"DEFAULT_SYSTEM_VOLTAGE": 0, "DEFAULT_REF_DISTANCE": "10"})
    def test_non_positive_numbers(self):
        self.assertEqual(ids(check_settings()), ["trainhorn.E003", "trainhorn.E003"])

    @override_settings(TRAINHORN={"DEFAULT_MAX_DROP_PCT": 60})
    def test_drop_too_high(self):
        self.assertEqual(ids(check_settings()), ["trainhorn.E004"])

    @override_settings(TRAINHORN={"DECIMALS": True})
    def test_bad_decimals(self):
        self.assertEqual(ids(check_settings()), ["trainhorn.E005"])

    @override_settings(TRAINHORN={"DEFAULT_UNITS": "m"})
    def test_unknown_key_warns(self):
        messages = check_settings()
        self.assertEqual(ids(messages), ["trainhorn.W001"])
        self.assertIn("DEFAULT_UNIT", messages[0].hint)

    @override_settings(TRAINHORN={"DEFAULT_UNIT": "m", "DEFAULT_REF_DISTANCE": 1, "DEFAULT_SYSTEM_VOLTAGE": 24,
                                  "DEFAULT_MAX_DROP_PCT": 2.5, "DECIMALS": 2})
    def test_full_valid_config(self):
        self.assertEqual(check_settings(), [])
