"""Rules for the names that end up as C++ identifiers."""

from __future__ import annotations

import re

from ..diagnostics import Source

IDENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")

CPP_KEYWORDS = frozenset({
    "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor", "bool", "break",
    "case", "catch", "char", "char8_t", "char16_t", "char32_t", "class", "compl", "concept",
    "const", "consteval", "constexpr", "constinit", "const_cast", "continue", "co_await",
    "co_return", "co_yield", "decltype", "default", "delete", "do", "double", "dynamic_cast",
    "else", "enum", "explicit", "export", "extern", "false", "float", "for", "friend", "goto",
    "if", "inline", "int", "long", "mutable", "namespace", "new", "noexcept", "not", "not_eq",
    "nullptr", "operator", "or", "or_eq", "private", "protected", "public", "register",
    "reinterpret_cast", "requires", "return", "short", "signed", "sizeof", "static",
    "static_assert", "static_cast", "struct", "switch", "template", "this", "thread_local",
    "throw", "true", "try", "typedef", "typeid", "typename", "union", "unsigned", "using",
    "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq",
})


def is_identifier(value: object) -> bool:
    return isinstance(value, str) and bool(IDENT_RE.match(value))


def check_identifier(source: Source, key: str, value: object, what: str, *,
                     cpp_name: bool = False, enum_member: bool = False) -> bool:
    """Check a snake_case name.

    cpp_name: the name is emitted as a C++ variable, so keywords are forbidden.
    enum_member: the name becomes an enum value next to COUNT.
    """
    if not is_identifier(value):
        source.error(key, f"invalid {what} '{value}' (expected snake_case: [a-z][a-z0-9_]*)")
        return False
    if cpp_name and value in CPP_KEYWORDS:
        source.error(key, f"{what} '{value}' is a C++ keyword")
        return False
    if enum_member and value == "count":
        source.error(key, f"{what} 'count' is reserved (it would clash with COUNT)")
        return False
    return True
