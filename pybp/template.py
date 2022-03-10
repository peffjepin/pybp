import re
import datetime
import pathlib

from typing import List
from typing import Iterable

from . import config


_STATIC_TEMPLATE_NAMESPACE = {"year": str(datetime.datetime.today().year)}
_EVAL_PATTERN = re.compile(r"{{(.+?)}}")
_CONDITIONAL_PATTERN = re.compile(r"({\?.+?\?})")


def render(text: str, namespace: dict = None) -> str:
    return _base_render(text, namespace)


def render_file(path: pathlib.Path, namespace: dict = None) -> str:
    with open(path, "r") as f:
        text = f.read()
    return _base_render(text, namespace)


def copy(
    template: pathlib.Path, target: pathlib.Path, namespace: dict = None
) -> None:
    with open(target, "w") as f:
        f.write(render_file(template, namespace))


def _base_render(text: str, namespace: dict) -> str:
    # all render requests should get routed through here so that
    # we can manipulate the namespace internally however we like
    if namespace is None:
        namespace = {}
    namespace = {
        **namespace,
        **_STATIC_TEMPLATE_NAMESPACE,
        **config.PersistantUserConfig.get_dict(),
    }
    chunks = _resolve_conditional_blocks(text, namespace)
    return "".join(
        map(lambda chunk: _resolve_eval_blocks(chunk, namespace), chunks)
    )


def _resolve_conditional_blocks(text: str, namespace: dict) -> List[str]:
    good_chunks = []
    all_chunks = _CONDITIONAL_PATTERN.split(text)
    i = 0

    def add_chunk(chunk):
        # avoid adding a ton of line breaks from the conditional block syntax
        prev_ends_with_newline = good_chunks and good_chunks[-1].endswith("\n")
        if prev_ends_with_newline and chunk.startswith("\n"):
            chunk = chunk[1:]
        if not chunk:
            return
        good_chunks.append(chunk)

    while i < len(all_chunks):
        chunk = all_chunks[i]

        if chunk.startswith("{?"):
            condition = chunk[2:-2].strip()
            if eval(condition, {}, namespace):
                add_chunk(all_chunks[i + 1][1:-1])
            # we are now done processing 3 chunks...
            # the i chunk (this chunk - the condition)
            # the i + 1 chunk (the conditional body)
            # the i + 2 chunk (the conditional end)
            i += 3
        else:
            if len(chunk) > 0:
                add_chunk(chunk)
            i += 1

    return good_chunks


def _resolve_eval_blocks(text: str, namespace: dict) -> str:
    return _EVAL_PATTERN.sub(
        lambda m: _expand_eval_block(eval(m.group(1).strip(), {}, namespace)),
        text,
    )


def _expand_eval_block(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Iterable):
        return "\n".join(map(str, value))
    else:
        return str(value)
