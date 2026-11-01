"""CSS-like selectors: [ancestor ] [parent > ]target, target = class(:state)*[::part].

A target without class, ':screen', means "an object without parent".
"""

from __future__ import annotations

import re

from ..diagnostics import Source
from ..model import Selector
from .identifiers import is_identifier

SCREEN = "screen"


def _split_context(text: str) -> tuple[str | None, str | None, str] | None:
    """Return (ancestor, parent, target), or None when the shape is not supported."""
    tokens = re.sub(r"\s*>\s*", " > ", text.strip()).split()
    words = [token for token in tokens if token != ">"]

    match tokens:
        case [target]:
            return None, None, target
        case [ancestor, target] if ">" not in tokens:
            return ancestor, None, target
        case [parent, ">", target] if len(words) == 2:
            return None, parent, target
        case [ancestor, parent, ">", target] if len(words) == 3:
            return ancestor, parent, target
    return None


def parse_selector(source: Source, key: str, text: object) -> Selector | None:
    if not isinstance(text, str) or not text.strip():
        source.error(key, "selector must be a non-empty string")
        return None

    context = _split_context(text)
    if context is None:
        source.error(key, f"invalid selector '{text}' (expected [ancestor ] [parent > ]target)")
        return None
    ancestor, parent, target_text = context

    ok = True
    for role, name in (("ancestor", ancestor), ("parent", parent)):
        if name is not None and not is_identifier(name):
            source.error(key, f"invalid {role} '{name}' in '{text}' (a class name only, no state or part)")
            ok = False

    base, has_part, part = target_text.partition("::")
    if has_part and not is_identifier(part):
        source.error(key, f"invalid part in '{text}'")
        ok = False

    cls, *states = base.split(":")
    for state in states:
        if not is_identifier(state):
            source.error(key, f"invalid state '{state}' in '{text}'")
            ok = False

    if cls == "":
        if states[:1] != [SCREEN]:
            source.error(key, f"missing class in '{text}'")
            ok = False
        target = None
        states = states[1:]
    else:
        if not is_identifier(cls):
            source.error(key, f"invalid class '{cls}' in '{text}'")
            ok = False
        target = cls

    if not ok:
        return None
    return Selector(target=target, parent=parent, ancestor=ancestor,
                    states=tuple(states), part=part or None)
