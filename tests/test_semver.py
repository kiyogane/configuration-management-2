"""Тесты требований к версиям (этап 3)."""

import unittest

from depviz.semver import matches, sort_key


class SemverTest(unittest.TestCase):
    """Проверки matches и sort_key."""

    def check(self, requirement, good, bad):
        """Версии good подходят под требование, bad — нет."""
        for version in good:
            with self.subTest(req=requirement, version=version):
                self.assertTrue(matches(requirement, version))
        for version in bad:
            with self.subTest(req=requirement, version=version):
                self.assertFalse(matches(requirement, version))

    def test_caret(self):
        """Оператор ^ и требование без оператора."""
        self.check("^1.2.3", ["1.2.3", "1.9.0"], ["1.2.2", "2.0.0"])
        self.check("1.2", ["1.2.0", "1.99.1"], ["1.1.9", "2.0.0"])
        self.check("^0.2", ["0.2.0", "0.2.9"], ["0.3.0", "0.1.9"])
        self.check("^0.0.3", ["0.0.3"], ["0.0.4", "0.0.2"])
        self.check("^0", ["0.0.1", "0.9.9"], ["1.0.0"])

    def test_tilde_exact_wildcard(self):
        """Операторы ~, = и шаблоны *."""
        self.check("~2.4.0", ["2.4.0", "2.4.7"], ["2.5.0", "2.3.9"])
        self.check("~1", ["1.0.0", "1.9.9"], ["2.0.0"])
        self.check("=1.0.200", ["1.0.200"], ["1.0.201", "1.0.199"])
        self.check("*", ["0.0.1", "9.9.9"], [])
        self.check("1.*", ["1.0.0", "1.5.0"], ["2.0.0", "0.9.0"])

    def test_ranges(self):
        """Сравнения и их комбинации через запятую."""
        self.check(">=0.3, <0.5", ["0.3.0", "0.4.9"], ["0.2.9", "0.5.0"])
        self.check(">1.2", ["1.3.0"], ["1.2.9"])
        self.check("<=1.2", ["1.2.9"], ["1.3.0"])
        self.check(">1.2.3", ["1.2.4"], ["1.2.3"])

    def test_bad_requirement(self):
        """Некорректное требование вызывает ValueError."""
        with self.assertRaises(ValueError):
            matches("^^1", "1.0.0")

    def test_sort_key(self):
        """Пре-релиз меньше релиза той же версии."""
        versions = ["1.0.0", "1.0.0-beta", "0.9.0", "1.0.1"]
        ordered = sorted(versions, key=sort_key)
        self.assertEqual(ordered, ["0.9.0", "1.0.0-beta", "1.0.0", "1.0.1"])


if __name__ == "__main__":
    unittest.main()
