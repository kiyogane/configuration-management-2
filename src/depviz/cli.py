"""Интерфейс командной строки."""

import argparse
import sys

from depviz.config import DEFAULT_REPO, ConfigError, make_config

EXIT_CONFIG_ERROR = 2


def build_parser():
    """Создать парсер опций командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Визуализатор графа зависимостей пакетов Cargo",
    )
    parser.add_argument("--package", default="",
                        help="имя анализируемого пакета")
    parser.add_argument("--repo", default=DEFAULT_REPO,
                        help="URL репозитория или путь к тестовому файлу")
    parser.add_argument("--test-mode", action="store_true",
                        help="работать с тестовым репозиторием (файлом)")
    parser.add_argument("--version", default=None,
                        help="версия пакета, например 1.0.200")
    parser.add_argument("--filter", default="",
                        help="не учитывать пакеты с этой подстрокой")
    return parser


def print_pairs(pairs):
    """Вывести пары ключ-значение."""
    for key, value in pairs:
        print(f"{key}={value}")


def main(argv=None):
    """Точка входа: разобрать опции и вывести параметры."""
    args = build_parser().parse_args(argv)
    try:
        config = make_config(args)
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    print_pairs(config.as_pairs())
    return 0
