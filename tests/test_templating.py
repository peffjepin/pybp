import pytest
from pybp import template


def test_templating_happy_path():
    random_lines = ["ashfkajgfh", "gfa kashgjkl{a{sf asldg;hh} a"]
    template_line = "{{ greeting }} my name is {{ name }}"
    injected_line = "hi my name is John Doe"

    test_text = "\n".join((*random_lines, template_line, *random_lines))
    expected = "\n".join((*random_lines, injected_line, *random_lines))

    actual = template.inject(test_text, {"name": "John Doe", "greeting": "hi"})
    assert actual == expected


def test_templating_non_template():
    my_regular_text = "this is not actually a template"

    assert template.inject(my_regular_text, {}) == my_regular_text


def test_templating_error_path():
    random_lines = ["ashfkajgfh", "gfa kashgjkl{a{sf asldg;hh} a"]
    template_line = "{{ greeting }} my name is {{ name }}"
    test_text = "\n".join((*random_lines, template_line, *random_lines))

    with pytest.raises(KeyError):
        template.inject(test_text, {"name": "John Doe"})
