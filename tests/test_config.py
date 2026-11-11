"""Тесты проверки параметров (этап 1)."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr

from depviz.cli import EXIT_CONFIG_ERROR, build_parser, main
from depviz.config import ConfigError, make_config


def parse(argv):
    """Разобрать опции и собрать Config."""
    return make_config(build_parser().parse_args(argv))


class ConfigTest(unittest.TestCase):
    """Проверки make_config."""

    def setUp(self):
        """Создать временный файл тестового репозитория."""
        handle, self.repo_file = tempfile.mkstemp(suffix=".txt")
        os.close(handle)

    def tearDown(self):
        """Удалить временный файл."""
        os.remove(self.repo_file)

    def test_valid_real_mode(self):
        """Корректные параметры для crates.io."""
        cfg = parse(["--package", "serde", "--version", "1.0.200"])
        self.assertEqual(cfg.package, "serde")
        self.assertFalse(cfg.test_mode)
        self.assertEqual(cfg.repo, "https://index.crates.io")
        self.assertEqual(cfg.output, os.path.join("out", "serde.puml"))

    def test_valid_test_mode(self):
        """Корректные параметры для тестового репозитория."""
        cfg = parse(["--package", "A", "--test-mode",
                     "--repo", self.repo_file, "--filter", "X"])
        self.assertTrue(cfg.test_mode)
        self.assertIsNone(cfg.version)

    def test_errors(self):
        """Каждый ошибочный параметр дает ConfigError."""
        bad = [
            [],
            ["--package", "bad name!", "--version", "1.0.0"],
            ["--package", "serde"],
            ["--package", "serde", "--version", "1.x"],
            ["--package", "serde", "--version", "1.0.0", "--repo", "ftp:/x"],
            ["--package", "a", "--test-mode", "--repo", self.repo_file],
            ["--package", "A", "--test-mode", "--repo", "/no/such/file"],
            ["--package", "serde", "--version", "1.0.0", "--filter", "ser"],
            ["--package", "serde", "--version", "1.0.0", "--filter", " x"],
            ["--package", "serde", "--version", "1.0.0", "--reverse"],
            ["--package", "serde", "--version", "1.0.0", "--output", "g.png"],
        ]
        for argv in bad:
            with self.subTest(argv=argv):
                with self.assertRaises(ConfigError):
                    parse(argv)

    def test_pairs(self):
        """Параметры выводятся парами ключ-значение."""
        cfg = parse(["--package", "serde", "--version", "1.0.200"])
        pairs = dict(cfg.as_pairs())
        self.assertEqual(pairs["package"], "serde")
        self.assertEqual(pairs["version"], "1.0.200")

    def test_main_error_code(self):
        """При ошибке main возвращает код и пишет в stderr."""
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["--package", "serde"])
        self.assertEqual(code, EXIT_CONFIG_ERROR)
        self.assertIn("Ошибка", err.getvalue())


if __name__ == "__main__":
    unittest.main()
