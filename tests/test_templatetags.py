from django.template import Context, Template
from django.test import SimpleTestCase, override_settings

from trainhorn.templatetags import trainhorn as tags


def render(source, **context):
    return Template("{% load trainhorn %}" + source).render(Context(context))


class FilterTests(SimpleTestCase):
    def test_spl_at_distance_reference_vector(self):
        self.assertEqual(render('{{ 150|spl_at_distance:"10,100" }}'), "130.0")

    def test_spl_at_distance_default_reference(self):
        self.assertEqual(render('{{ 150|spl_at_distance:"100" }}'), "130.0")

    def test_spl_at_distance_metres(self):
        self.assertEqual(render('{{ 120|spl_at_distance:"1,10,m" }}'), "100.0")

    def test_spl_from_variable(self):
        self.assertEqual(render('{{ db|spl_at_distance:"10,100" }}', db="150"), "130.0")

    def test_distance_for_spl(self):
        self.assertEqual(render('{{ 150|distance_for_spl:"10,130" }}'), "100.0")
        self.assertEqual(render('{{ 150|distance_for_spl:"130" }}'), "100.0")

    def test_tank_runtime(self):
        self.assertEqual(render('{{ 5|tank_runtime:"150,110,10" }}'), "10.9")

    def test_awg(self):
        self.assertEqual(render('{{ 30|awg:"10" }}'), "6")
        self.assertEqual(render('{{ 30|awg:"10,24,3,ft" }}'), tags._wire(30, ["10", "24", "3", "ft"]).awg)

    def test_voltage_drop(self):
        value = tags.voltage_drop(30, "10,8")
        self.assertGreater(value, 0)
        self.assertEqual(render('{{ 30|voltage_drop:"10,8" }}'), str(value))

    def test_invalid_input_renders_empty(self):
        self.assertEqual(render('{{ 150|spl_at_distance:"0,100" }}'), "")
        self.assertEqual(render('{{ "loud"|spl_at_distance:"10,100" }}'), "")
        self.assertEqual(render('{{ 150|spl_at_distance:"1,2,3,4" }}'), "")
        self.assertEqual(render('{{ 5|tank_runtime:"100,110,10" }}'), "")
        self.assertEqual(render('{{ 5|tank_runtime:"150" }}'), "")
        self.assertEqual(render('{{ 30|awg:"" }}'), "")
        self.assertEqual(render('{{ 5000|awg:"500" }}'), "")
        self.assertEqual(render('{{ 30|voltage_drop:"10,99" }}'), "")

    @override_settings(TRAINHORN={"DECIMALS": 3, "DEFAULT_UNIT": "m", "DEFAULT_REF_DISTANCE": 1})
    def test_settings_change_defaults(self):
        self.assertEqual(render('{{ 5|tank_runtime:"150,110,10" }}'), "10.916")
        self.assertEqual(render('{{ 120|spl_at_distance:"10" }}'), "100.0")

    def test_wire_tag(self):
        out = render("{% trainhorn_wire 30 10 as wire %}{{ wire.awg }}|{{ wire.voltage_drop_pct|floatformat:2 }}")
        self.assertEqual(out, "6|1.98")

    def test_wire_tag_invalid(self):
        out = render("{% trainhorn_wire 0 10 as wire %}[{% if wire is None %}none{% endif %}]")
        self.assertEqual(out, "[none]")
