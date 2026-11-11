"""Интерфейс командной строки."""

import argparse
import os
import subprocess
import sys

from depviz.cargo import RepoError
from depviz.config import DEFAULT_REPO, ConfigError, make_config
from depviz.graph import build_graph, edge_count, find_cycle
from depviz.plantuml import show_image, to_plantuml
from depviz.repository import open_repository

EXIT_CONFIG_ERROR = 2
EXIT_REPO_ERROR = 3
EXIT_IO_ERROR = 4


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
    parser.add_argument("--reverse", action="store_true",
                        help="вывести обратные зависимости пакета")
    parser.add_argument("--output", default="",
                        help="файл PlantUML (по умолчанию out/ИМЯ.puml)")
    parser.add_argument("--image", action="store_true",
                        help="показать изображение графа")
    return parser


def print_adjacency(graph, arrow):
    """Вывести граф списком смежности."""
    for node, deps in graph.items():
        targets = ", ".join(dep.label() for dep in deps) or "(нет)"
        print(f"  {node.label()} {arrow} {targets}")


def print_users(graph, root):
    """Вывести пакеты, зависящие от анализируемого."""
    users = [node.label() for node in graph if node != root]
    print(f"От {root.label()} зависят: {', '.join(users) or '(никто)'}")


def print_cycle(graph, arrow):
    """Вывести найденный цикл, если он есть."""
    cycle = find_cycle(graph)
    if cycle:
        path = f" {arrow} ".join(node.label() for node in cycle)
        print(f"Обнаружена циклическая зависимость: {path}")


def print_graph(graph, root, reverse=False):
    """Вывести граф, зависящие пакеты (для --reverse) и цикл."""
    title = "Обратные зависимости" if reverse else "Граф зависимостей"
    arrow = "<-" if reverse else "->"
    print(f"{title} {root.label()} (пакетов: {len(graph)}, "
          f"связей: {edge_count(graph)})")
    print_adjacency(graph, arrow)
    if reverse:
        print_users(graph, root)
    print_cycle(graph, arrow)


def save_plantuml(graph, root, config):
    """Сохранить PlantUML-описание, вывести его и при желании картинку."""
    text = to_plantuml(graph, root, config.reverse)
    folder = os.path.dirname(config.output)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(config.output, "w", encoding="utf-8") as file:
        file.write(text)
    print(f"\nPlantUML ({config.output}):")
    print(text, end="")
    if config.image:
        show_image(config.output, text)


def run(config):
    """Построить граф по параметрам, вывести его и визуализировать."""
    repo = open_repository(config)
    root = repo.root(config.package, config.version)
    graph = build_graph(repo, root, config.filter)
    print_graph(graph, root, config.reverse)
    save_plantuml(graph, root, config)


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
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Ошибка ввода-вывода: {error}", file=sys.stderr)
        return EXIT_IO_ERROR
    return 0
