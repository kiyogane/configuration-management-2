"""Чтение данных о пакетах из sparse-индекса crates.io.

Формат индекса: https://doc.rust-lang.org/cargo/reference/registry-index.html
Каждая строка файла пакета — JSON-описание одной версии с полем deps.
"""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from depviz import semver

USER_AGENT = "depviz-study (configuration-management practice)"
TIMEOUT_SECONDS = 20
HTTP_NOT_FOUND = 404
SHORT_NAME_DIRS = {1: "1", 2: "2"}
THREE_LETTERS = 3
REQUIRED_KINDS = ("normal", "build")
SHOWN_VERSIONS = 5


class RepoError(Exception):
    """Ошибка получения данных из репозитория."""


@dataclass(frozen=True)
class Dependency:
    """Прямая зависимость из описания версии пакета."""

    name: str
    req: str
    kind: str
    optional: bool
    target: str | None
    feature_name: str = ""

    def is_required(self, enabled=frozenset()):
        """Нужна ли зависимость при сборке с включенными фичами."""
        if self.kind not in REQUIRED_KINDS:
            return False
        return not self.optional or self.feature_name in enabled


def index_path(name):
    """Вернуть путь к файлу пакета внутри индекса."""
    name = name.lower()
    size = len(name)
    if size in SHORT_NAME_DIRS:
        return f"{SHORT_NAME_DIRS[size]}/{name}"
    if size == THREE_LETTERS:
        return f"3/{name[0]}/{name}"
    return f"{name[0:2]}/{name[2:4]}/{name}"


def fetch_text(url):
    """Скачать текст по URL, ошибки превратить в RepoError."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise RepoError(f"пакет не найден: {url}") from error
        raise RepoError(f"HTTP {error.code} при запросе {url}") from error
    except urllib.error.URLError as error:
        raise RepoError(f"нет доступа к {url}: {error.reason}") from error


def parse_entries(text):
    """Разобрать файл индекса в список описаний версий."""
    entries = []
    for line in text.splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def fetch_entries(repo_url, name):
    """Получить все версии пакета из индекса по URL репозитория."""
    url = f"{repo_url.rstrip('/')}/{index_path(name)}"
    return parse_entries(fetch_text(url))


def find_version(entries, version):
    """Найти описание заданной версии пакета."""
    for entry in entries:
        if entry["vers"] == version:
            return entry
    latest = ", ".join(entry["vers"] for entry in entries[-SHOWN_VERSIONS:])
    raise RepoError(f"версия {version} не найдена (последние: {latest})")


def fits(requirement, version):
    """semver.matches, но с ошибкой репозитория вместо ValueError."""
    try:
        return semver.matches(requirement, version)
    except ValueError as error:
        raise RepoError(str(error)) from error


def select_version(entries, requirement):
    """Выбрать наибольшую версию, подходящую под требование.

    Как и Cargo, сначала рассматриваются релизы без пометки yanked,
    затем пре-релизы, затем отозванные (yanked) версии.
    """
    groups = (
        [e for e in entries if not e.get("yanked") and "-" not in e["vers"]],
        [e for e in entries if not e.get("yanked")],
        entries,
    )
    for group in groups:
        suitable = [e for e in group if fits(requirement, e["vers"])]
        if suitable:
            return max(suitable, key=lambda e: semver.sort_key(e["vers"]))
    name = entries[0]["name"] if entries else "?"
    raise RepoError(f"нет версии {name}, подходящей под '{requirement}'")


def expand_feature(item, features, enabled, queue):
    """Обработать один элемент списка фич."""
    if item.startswith("dep:"):
        enabled.add(item[len("dep:"):])
    elif "/" in item:
        dep_name = item.split("/")[0]
        if not dep_name.endswith("?"):
            enabled.add(dep_name)
    elif item in features:
        queue.extend(features[item])
    else:
        enabled.add(item)


def default_features(entry):
    """Имена опциональных зависимостей, включенных фичей default."""
    features = dict(entry.get("features") or {})
    features.update(entry.get("features2") or {})
    enabled, seen = set(), set()
    queue = list(features.get("default", []))
    while queue:
        item = queue.pop()
        if item not in seen:
            seen.add(item)
            expand_feature(item, features, enabled, queue)
    return enabled


def parse_dependency(raw):
    """Преобразовать JSON-описание зависимости в Dependency."""
    return Dependency(
        name=raw.get("package") or raw["name"],
        req=raw["req"],
        kind=raw.get("kind") or "normal",
        optional=raw.get("optional", False),
        target=raw.get("target"),
        feature_name=raw["name"],
    )


def direct_dependencies(entry):
    """Вернуть все прямые зависимости версии пакета."""
    return [parse_dependency(raw) for raw in entry["deps"]]


def required_dependencies(entry):
    """Зависимости, нужные при сборке с фичами по умолчанию.

    dev-зависимости отбрасываются, опциональные остаются, только если
    их включает фича default. Повторы (одна зависимость для разных
    платформ) объединяются по имени.
    """
    enabled = default_features(entry)
    result = {}
    for dep in direct_dependencies(entry):
        if dep.is_required(enabled) and dep.name not in result:
            result[dep.name] = dep
    return list(result.values())
