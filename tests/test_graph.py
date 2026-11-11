"""Тесты построения графа и тестового репозитория (этап 3)."""

import io
import os
import unittest
from contextlib import redirect_stdout

from depviz.cargo import RepoError
from depviz.cli import main
from depviz.graph import build_graph, find_cycle
from depviz.repository import Node, TestRepository

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples", "repos")


def example(name):
    """Путь к файлу тестового репозитория из examples/repos."""
    return os.path.join(EXAMPLES, name)


def names(graph):
    """Граф в виде {имя: [имена зависимостей]}."""
    return {n.name: [d.name for d in deps] for n, deps in graph.items()}


class GraphTest(unittest.TestCase):
    """Проверки BFS, фильтра и циклов."""

    def build(self, file_name, substring=""):
        """Построить граф от пакета A из тестового файла."""
        repo = TestRepository(example(file_name))
        return build_graph(repo, repo.root("A"), substring)

    def test_bfs_order(self):
        """Вершины перечисляются по уровням BFS."""
        graph = self.build("simple.txt")
        self.assertEqual(list(names(graph)), ["A", "B", "C", "D", "E"])
        self.assertIsNone(find_cycle(graph))

    def test_cycle(self):
        """Цикл не зацикливает обход и обнаруживается."""
        graph = self.build("cycle.txt")
        self.assertEqual(set(names(graph)), {"A", "B", "C", "D"})
        cycle = [node.name for node in find_cycle(graph)]
        self.assertEqual(cycle, ["A", "B", "C", "A"])

    def test_filter(self):
        """Пакеты с подстрокой и их «хвосты» исключаются."""
        graph = names(self.build("filter.txt", "B"))
        self.assertEqual(graph, {"A": ["C"], "C": ["XD"], "XD": []})
        graph = names(self.build("filter.txt", "X"))
        self.assertEqual(graph, {"A": ["C"], "C": []})

    def test_undescribed_leaf(self):
        """Неописанный в файле пакет — лист."""
        graph = names(self.build("diamond.txt"))
        self.assertEqual(graph["Z"], [])
        self.assertEqual(graph["D"], ["Z"])

    def test_bad_files(self):
        """Ошибки формата файла и отсутствующий пакет."""
        with self.assertRaises(RepoError):
            TestRepository(example("broken.txt"))
        with self.assertRaises(RepoError):
            TestRepository(example("simple.txt")).root("Q")

    def test_node_label(self):
        """Подпись вершины с версией и без."""
        self.assertEqual(Node("serde", "1.0.0").label(), "serde 1.0.0")
        self.assertEqual(Node("A").label(), "A")

    def test_main_test_mode(self):
        """main в тестовом режиме печатает граф и цикл."""
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["--package", "A", "--test-mode",
                         "--repo", example("cycle.txt")])
        self.assertEqual(code, 0)
        self.assertIn("A -> B", out.getvalue())
        self.assertIn("циклическая зависимость: A -> B -> C -> A",
                      out.getvalue())


if __name__ == "__main__":
    unittest.main()
