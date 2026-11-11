"""Интерфейс командной строки."""

import argparse
import sys

from depviz.cargo import RepoError
from depviz.config import DEFAULT_REPO, ConfigError, make_config
from depviz.graph import build_graph, edge_count, find_cycle
from depviz.repository import open_repository

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


def print_graph(graph, root):
    """Вывести граф списком смежности и сведения о циклах."""
    print(f"Граф зависимостей {root.label()} (пакетов: {len(graph)}, "
          f"связей: {edge_count(graph)})")
    for node, deps in graph.items():
        targets = ", ".join(dep.label() for dep in deps) or "(нет)"
        print(f"  {node.label()} -> {targets}")
    cycle = find_cycle(graph)
    if cycle:
        path = " -> ".join(node.label() for node in cycle)
        print(f"Обнаружена циклическая зависимость: {path}")


def run(config):
    """Построить граф по параметрам и вывести его."""
    repo = open_repository(config)
    root = repo.root(config.package, config.version)
    graph = build_graph(repo, root, config.filter)
    print_graph(graph, root)


def main(argv=None):
    """Точка входа: разобрать опции и вывести граф зависимостей."""
    args = build_parser().parse_args(argv)
    try:
        config = make_config(args)
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    try:
        run(config)
    except RepoError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_REPO_ERROR
    return 0
