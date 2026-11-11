"""Источники графа: реальный репозиторий Cargo и тестовый файл."""

import re
from dataclasses import dataclass

from depviz import cargo

TEST_NAME_RE = re.compile(r"^[A-Z]+$")


@dataclass(frozen=True)
class Node:
    """Вершина графа: пакет конкретной версии."""

    name: str
    version: str = ""

    def label(self):
        """Подпись вершины для вывода."""
        return f"{self.name} {self.version}".strip()


class CargoRepository:
    """Граф пакетов из sparse-индекса crates.io."""

    def __init__(self, url):
        """Запомнить URL индекса, подготовить кэш."""
        self.url = url
        self.cache = {}

    def entries(self, name):
        """Все версии пакета (с кэшированием)."""
        if name not in self.cache:
            self.cache[name] = cargo.fetch_entries(self.url, name)
        return self.cache[name]

    def root(self, name, version):
        """Вершина для анализируемого пакета."""
        entry = cargo.find_version(self.entries(name), version)
        return Node(entry["name"], entry["vers"])

    def dependencies(self, node):
        """Прямые зависимости вершины с подобранными версиями."""
        entry = cargo.find_version(self.entries(node.name), node.version)
        result = []
        for dep in cargo.required_dependencies(entry):
            chosen = cargo.select_version(self.entries(dep.name), dep.req)
            result.append(Node(chosen["name"], chosen["vers"]))
        return result


def parse_test_line(line, number):
    """Разобрать строку 'A: B C' тестового репозитория."""
    if ":" not in line:
        raise cargo.RepoError(f"строка {number}: нет символа ':'")
    head, tail = line.split(":", 1)
    names = [head.strip()] + tail.split()
    for name in names:
        if not TEST_NAME_RE.match(name):
            raise cargo.RepoError(
                f"строка {number}: недопустимое имя пакета '{name}'"
            )
    return names[0], names[1:]


def load_test_graph(path):
    """Прочитать файл тестового репозитория в словарь смежности."""
    graph = {}
    with open(path, encoding="utf-8") as file:
        for number, raw in enumerate(file, 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            name, deps = parse_test_line(line, number)
            if name in graph:
                raise cargo.RepoError(
                    f"строка {number}: пакет {name} описан повторно"
                )
            graph[name] = deps
    return graph


class GraphRepository:
    """Граф пакетов, заданный словарем смежности {имя: [имена]}."""

    def __init__(self, graph):
        """Запомнить словарь смежности."""
        self.graph = graph

    def known(self, name):
        """Упомянут ли пакет в графе (слева или справа)."""
        if name in self.graph:
            return True
        return any(name in deps for deps in self.graph.values())

    def root(self, name, version=None):
        """Вершина для анализируемого пакета (версия не используется)."""
        if not self.known(name):
            raise cargo.RepoError(f"пакет {name} не описан в файле")
        return Node(name)

    def dependencies(self, node):
        """Прямые зависимости; неописанный пакет считается листом."""
        return [Node(name) for name in self.graph.get(node.name, [])]

    def reversed(self):
        """Репозиторий с обращенными ребрами: кто зависит от пакета."""
        reverse = {}
        for name, deps in self.graph.items():
            for dep in deps:
                reverse.setdefault(dep, []).append(name)
        return GraphRepository(reverse)


class TestRepository(GraphRepository):
    """Граф пакетов из файла, пакеты — большие латинские буквы."""

    def __init__(self, path):
        """Загрузить описание графа из файла."""
        super().__init__(load_test_graph(path))


def open_repository(config):
    """Создать репозиторий по параметрам запуска."""
    if not config.test_mode:
        return CargoRepository(config.repo)
    repo = TestRepository(config.repo)
    return repo.reversed() if config.reverse else repo
