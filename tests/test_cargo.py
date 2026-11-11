"""Тесты чтения индекса crates.io (этап 2)."""

import io
import json
import unittest
import urllib.error
from contextlib import redirect_stdout
from unittest import mock

from depviz import cargo
from depviz.cli import main

ENTRY_OLD = {"name": "demo", "vers": "0.1.0", "deps": []}
ENTRY = {
    "name": "demo",
    "vers": "1.0.0",
    "deps": [
        {"name": "libc", "req": "^0.2", "kind": "normal",
         "optional": False, "target": None},
        {"name": "cc", "req": "^1", "kind": "build",
         "optional": False, "target": None},
        {"name": "serde", "req": "^1", "kind": "normal",
         "optional": True, "target": None},
        {"name": "quickcheck", "req": "^1", "kind": "dev",
         "optional": False, "target": None},
        {"name": "alias", "package": "real-name", "req": "=2.0.0",
         "optional": False, "target": "cfg(unix)"},
    ],
}
INDEX_TEXT = "\n".join(json.dumps(e) for e in (ENTRY_OLD, ENTRY)) + "\n"


class FakeResponse(io.BytesIO):
    """Ответ urlopen, поддерживающий with."""

    def __enter__(self):
        """Вернуть себя."""
        return self

    def __exit__(self, *args):
        """Ничего не делать."""
        return False


class CargoTest(unittest.TestCase):
    """Проверки модуля cargo."""

    def test_index_path(self):
        """Путь в индексе зависит от длины имени."""
        self.assertEqual(cargo.index_path("a"), "1/a")
        self.assertEqual(cargo.index_path("cc"), "2/cc")
        self.assertEqual(cargo.index_path("syn"), "3/s/syn")
        self.assertEqual(cargo.index_path("Serde"), "se/rd/serde")

    def test_find_version(self):
        """Поиск версии и ошибка для отсутствующей."""
        entries = cargo.parse_entries(INDEX_TEXT)
        self.assertEqual(cargo.find_version(entries, "1.0.0"), ENTRY)
        with self.assertRaises(cargo.RepoError):
            cargo.find_version(entries, "9.9.9")

    def test_direct_dependencies(self):
        """Разбор зависимостей: вид, optional, переименование."""
        deps = cargo.direct_dependencies(ENTRY)
        names = [d.name for d in deps]
        self.assertEqual(names,
                         ["libc", "cc", "serde", "quickcheck", "real-name"])
        required = [d.name for d in deps if d.is_required()]
        self.assertEqual(required, ["libc", "cc", "real-name"])

    def test_fetch_entries(self):
        """Запрос идет по правильному URL."""
        fake = FakeResponse(INDEX_TEXT.encode())
        with mock.patch("urllib.request.urlopen", return_value=fake) as op:
            entries = cargo.fetch_entries("https://index.crates.io/", "demo")
        self.assertEqual(len(entries), 2)
        url = op.call_args.args[0].full_url
        self.assertEqual(url, "https://index.crates.io/de/mo/demo")

    def test_not_found(self):
        """HTTP 404 превращается в RepoError."""
        error = urllib.error.HTTPError("u", 404, "nf", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(cargo.RepoError):
                cargo.fetch_entries("https://index.crates.io", "nope")

    def test_main_prints_direct(self):
        """main выводит прямые зависимости."""
        fake = FakeResponse(INDEX_TEXT.encode())
        out = io.StringIO()
        with mock.patch("urllib.request.urlopen", return_value=fake):
            with redirect_stdout(out):
                code = main(["--package", "demo", "--version", "1.0.0"])
        self.assertEqual(code, 0)
        self.assertIn("libc ^0.2 [normal]", out.getvalue())
        self.assertIn("serde ^1 [normal, optional]", out.getvalue())


if __name__ == "__main__":
    unittest.main()
