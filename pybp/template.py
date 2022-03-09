import re


def inject(template_text, template_vars):
    return re.sub(
        "({{)(.+?)(}})",
        lambda m: template_vars[(m.group(2).strip())],
        template_text,
    )
