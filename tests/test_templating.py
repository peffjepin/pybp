import pytest
from pybp import template


def test_injection_happy_path():
    test_text = """
line1
{{ greeting }} my name is {{ name }}
line3
"""
    expected = """
line1
hi my name is John Doe
line3
"""
    actual = template.render(test_text, {"name": "John Doe", "greeting": "hi"})
    assert actual == expected


def test_injection_does_not_modify_regular_text():
    my_regular_text = "this is not actually a template"

    assert template.render(my_regular_text, {}) == my_regular_text


def test_value_not_in_injection_namespace():
    test_text = "{{ hi }}"

    with pytest.raises(NameError):
        template.render(test_text, {"name": "John Doe"})


def test_template_value_is_not_a_string():
    assert template.render("{{ 1 + v }}", {"v": 3}) == "4"


def test_conditional_when_true():
    # we shouldnt get extra newlines
    test_text = """
line 1
{? True ?}
line 2
{? end ?}
line 3
"""
    expected = """
line 1
line 2
line 3
"""
    assert template.render(test_text) == expected


def test_conditional_when_false():
    # we shouldnt get extra newlines
    test_text = """
line 1
{? False ?}
line 2
{? end ?}
line 3
"""
    expected = """
line 1
line 3
"""
    assert template.render(test_text) == expected


def test_list_injections_are_newline_joined():
    test_text = """
line 1
{{ my_list }}
line 3
"""
    namespace = {"my_list": [1, 2, 3]}
    expected = """
line 1
1
2
3
line 3
"""
    assert template.render(test_text, namespace) == expected


def test_chained_conditionals_dont_add_whitespace():
    test_text = """
line 1
{? False ?}
line 2
{? end ?}
{? False ?}
line 3
{? end ?}
line 4
"""
    expected = """
line 1
line 4
"""
    assert template.render(test_text) == expected
