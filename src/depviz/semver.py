"""Минимальная поддержка требований к версиям в стиле Cargo.

Каждое требование (^1.2, ~0.3, >=1, <2, =1.0.5, 1.*, *) переводится
в полуинтервал [нижняя, верхняя) на тройках (major, minor, patch).
Несколько требований через запятую объединяются по «и».
"""

import re

MAJOR, MINOR, PATCH = 0, 1, 2
ONLY_MAJOR = 1
MAJOR_MINOR = 2
ZERO = (0, 0, 0)
WILDCARDS = ("*", "x", "X")

COMPARATOR_RE = re.compile(
    r"^\s*(\^|~|=|>=|<=|>|<)?\s*"
    r"([0-9xX*]+(?:\.[0-9xX*]+){0,2})"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\s*$"
)
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?")


def parse_version(text):
    """Разобрать версию 'X.Y.Z[-pre]' в ((X, Y, Z), pre)."""
    match = VERSION_RE.match(text)
    if not match:
        raise ValueError(f"некорректная версия: {text}")
    major, minor, patch, pre = match.groups()
    return (int(major), int(minor), int(patch)), pre or ""


def sort_key(text):
    """Ключ сортировки версий: пре-релиз меньше релиза."""
    numbers, pre = parse_version(text)
    return numbers, not pre, pre


def pad(parts):
    """Дополнить частичную версию нулями до тройки."""
    return tuple(parts) + (0,) * (PATCH + 1 - len(parts))


def bump(parts, index):
    """Увеличить компонент index, следующие обнулить."""
    raised = list(pad(parts))
    raised[index] += 1
    for position in range(index + 1, PATCH + 1):
        raised[position] = 0
    return tuple(raised)


def caret_index(parts):
    """Какой компонент увеличивать для оператора ^."""
    if parts[MAJOR] or len(parts) == ONLY_MAJOR:
        return MAJOR
    if parts[MINOR] or len(parts) == MAJOR_MINOR:
        return MINOR
    return PATCH


def last(parts):
    """Индекс последнего заданного компонента."""
    return len(parts) - 1


BOUNDS = {
    "^": lambda p: (pad(p), bump(p, caret_index(p))),
    "~": lambda p: (pad(p), bump(p, MAJOR if len(p) == ONLY_MAJOR
                                 else MINOR)),
    "=": lambda p: (pad(p), bump(p, last(p))),
    ">": lambda p: (bump(p, last(p)), None),
    ">=": lambda p: (pad(p), None),
    "<": lambda p: (ZERO, pad(p)),
    "<=": lambda p: (ZERO, bump(p, last(p))),
}


def comparator_bounds(text):
    """Перевести одно требование в полуинтервал (low, high)."""
    match = COMPARATOR_RE.match(text)
    if not match:
        raise ValueError(f"некорректное требование к версии: {text}")
    operator, version = match.groups()
    parts = []
    for piece in version.split("."):
        if piece in WILDCARDS:
            operator = "="
            break
        parts.append(int(piece))
    if not parts:
        return ZERO, None
    return BOUNDS[operator or "^"](parts)


def matches(requirement, version):
    """Удовлетворяет ли версия требованию (через запятую — «и»)."""
    numbers, _ = parse_version(version)
    for comparator in requirement.split(","):
        low, high = comparator_bounds(comparator)
        if numbers < low or (high is not None and numbers >= high):
            return False
    return True
