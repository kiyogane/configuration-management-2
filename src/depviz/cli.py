"""Интерфейс командной строки."""

import argparse
import sys

from depviz import cargo
from depviz.config import DEFAULT_REPO, ConfigError, make_config

EXIT_CONFIG_ERROR = 2
EXIT_REPO_ERROR = 3


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


def describe(dep):
    """Строка с описанием прямой зависимости."""
    notes = [dep.kind]
    if dep.optional:
        notes.append("optional")
    if dep.target:
        notes.append(f"target={dep.target}")
    return f"  {dep.name} {dep.req} [{', '.join(notes)}]"


def print_direct(config):
    """Вывести все прямые зависимости заданной версии пакета."""
    entries = cargo.fetch_entries(config.repo, config.package)
    entry = cargo.find_version(entries, config.version)
    deps = cargo.direct_dependencies(entry)
    print(f"Прямые зависимости {config.package} {config.version}:")
    if not deps:
        print("  (нет)")
    for dep in deps:
        print(describe(dep))


def main(argv=None):
    """Точка входа: разобрать опции и вывести прямые зависимости."""
    args = build_parser().parse_args(argv)
    try:
        config = make_config(args)
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    if config.test_mode:
        print("Тестовый режим будет реализован на этапе 3")
        return 0
    try:
        print_direct(config)
    except cargo.RepoError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_REPO_ERROR
    return 0
