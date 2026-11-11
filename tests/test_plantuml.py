"""Тесты PlantUML-представления (этап 5)."""

import io
import os
import tempfile
import unittest
import zlib
from contextlib import redirect_stdout
from unittest import mock

from depviz import plantuml
from depviz.cli import main
from depviz.repository import Node

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples", "repos")


def decode(text):
    """Обратное преобразование к plantuml.encode."""
    bits = "".join(f"{plantuml.ALPHABET.index(c):06b}" for c in text)
    data = int(bits, 2).to_bytes(len(bits) // 8, "big")
    return zlib.decompressobj(-15).decompress(data).decode("utf-8")


class PlantUmlTest(unittest.TestCase):
    """Проверки to_plantuml, encode и show_image."""

    def setUp(self):
        """Небольшой граф с циклом."""
        self.a, self.b, self.c = Node("A"), Node("B", "1.0.0"), Node("C")
        self.graph = {self.a: [self.b], self.b: [self.c], self.c: [self.a]}

    def test_text(self):
        """Описание содержит вершины, ребра и выделенный корень."""
        text = plantuml.to_plantuml(self.graph, self.a)
        lines = text.splitlines()
        self.assertEqual(lines[0], "@startuml")
        self.assertEqual(lines[-1], "@enduml")
        self.assertIn('rectangle "A" as n0 #LightBlue', lines)
        self.assertIn('rectangle "B 1.0.0" as n1', lines)
        self.assertIn("n2 --> n0", lines)

    def test_reverse_text(self):
        """В обратном режиме ребра ведут к анализируемому пакету."""
        graph = {self.a: [self.b], self.b: []}
        lines = plantuml.to_plantuml(graph, self.a, True).splitlines()
        self.assertIn("n1 --> n0", lines)
        self.assertIn("title Обратные зависимости A", lines)

    def test_encode_round_trip(self):
        """Закодированный текст раскодируется обратно."""
        text = plantuml.to_plantuml(self.graph, self.a)
        self.assertEqual(decode(plantuml.encode(text)).rstrip("\0"), text)
        url = plantuml.server_url(text)
        self.assertTrue(url.startswith(plantuml.SERVER + "/png/"))

    def test_show_image_fallback(self):
        """Без локального PlantUML открывается URL веб-сервера."""
        with mock.patch("shutil.which", return_value=None), \
                mock.patch("webbrowser.open") as browser, \
                redirect_stdout(io.StringIO()):
            plantuml.show_image("x.puml", "@startuml\n@enduml\n")
        self.assertTrue(browser.call_args.args[0].startswith("https://"))

    def test_main_writes_file(self):
        """main сохраняет .puml и печатает его."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "g.puml")
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--package", "A", "--test-mode",
                             "--repo", os.path.join(EXAMPLES, "simple.txt"),
                             "--output", path])
            self.assertEqual(code, 0)
            with open(path, encoding="utf-8") as file:
                self.assertIn("n0 --> n1", file.read())
        self.assertIn("@startuml", out.getvalue())


if __name__ == "__main__":
    unittest.main()
