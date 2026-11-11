"""Параметры запуска и их проверка."""

import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

DEFAULT_REPO = "https://index.crates.io"

CRATE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
TEST_NAME_RE = re.compile(r"^[A-Z]+$")
VERSION_RE = re.compile(
    r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$"
)
MAX_CRATE_NAME = 64
URL_SCHEMES = ("http", "https")
PUML_SUFFIX = ".puml"


class ConfigError(Exception):
    """Ошибка в параметрах, заданных пользователем."""


@dataclass(frozen=True)
class Config:
    """Проверенные параметры запуска."""

    package: str
    repo: str
    test_mode: bool
    version: str | None
    filter: str
    reverse: bool = False
    output: str = ""
    image: bool = False

    def as_pairs(self):
        """Вернуть параметры списком пар (ключ, значение)."""
        return [
            ("package", self.package),
            ("repo", self.repo),
            ("test_mode", self.test_mode),
            ("version", self.version),
            ("filter", self.filter),
            ("reverse", self.reverse),
            ("output", self.output),
            ("image", self.image),
        ]


def check_package(name, test_mode):
    """Проверить имя анализируемого пакета."""
    if not name:
        raise ConfigError("имя пакета не задано (--package)")
    if test_mode:
        if not TEST_NAME_RE.match(name):
            raise ConfigError(
                f"имя пакета '{name}': в тестовом режиме "
                "допустимы только большие латинские буквы"
            )
        return
    if len(name) > MAX_CRATE_NAME or not CRATE_NAME_RE.match(name):
        raise ConfigError(f"недопустимое имя пакета Cargo: '{name}'")


def check_repo(repo, test_mode):
    """Проверить URL репозитория или путь к тестовому файлу."""
    if not repo:
        raise ConfigError("репозиторий не задан (--repo)")
    if test_mode:
        if not os.path.isfile(repo):
            raise ConfigError(f"файл тестового репозитория не найден: {repo}")
        return
    url = urlparse(repo)
    if url.scheme not in URL_SCHEMES or not url.netloc:
        raise ConfigError(
            f"некорректный URL репозитория: '{repo}' "
            "(ожидается http:// или https://)"
        )


def check_version(version, test_mode):
    """Проверить версию пакета (в тестовом режиме она не нужна)."""
    if version is None:
        if test_mode:
            return
        raise ConfigError("версия пакета не задана (--version)")
    if not VERSION_RE.match(version):
        raise ConfigError(
            f"некорректная версия '{version}' (ожидается вида 1.2.3)"
        )


def check_filter(substring, package):
    """Проверить подстроку фильтрации пакетов."""
    if substring and substring.strip() != substring:
        raise ConfigError("подстрока фильтра не должна иметь пробелов по краям")
    if substring and substring in package:
        raise ConfigError(
            f"анализируемый пакет '{package}' содержит подстроку "
            f"фильтра '{substring}' и был бы исключен"
        )


def check_reverse(reverse, test_mode):
    """Обратные зависимости доступны только для тестового репозитория."""
    if reverse and not test_mode:
        raise ConfigError(
            "обратные зависимости (--reverse) поддерживаются только "
            "в тестовом режиме: индекс crates.io не хранит обратных связей"
        )


def check_output(path):
    """Проверить путь к файлу PlantUML."""
    if not path.endswith(PUML_SUFFIX):
        raise ConfigError(f"файл вывода должен иметь расширение .puml: {path}")
    folder = os.path.dirname(path)
    if folder and os.path.exists(folder) and not os.path.isdir(folder):
        raise ConfigError(f"не каталог: {folder}")


def default_output(package, reverse):
    """Путь к файлу PlantUML по умолчанию."""
    suffix = "-reverse" if reverse else ""
    return os.path.join("out", f"{package}{suffix}{PUML_SUFFIX}")


def make_config(args):
    """Собрать Config из результата argparse с проверкой всех полей."""
    check_package(args.package, args.test_mode)
    check_repo(args.repo, args.test_mode)
    check_version(args.version, args.test_mode)
    check_filter(args.filter, args.package)
    check_reverse(args.reverse, args.test_mode)
    output = args.output or default_output(args.package, args.reverse)
    check_output(output)
    return Config(
        package=args.package,
        repo=args.repo,
        test_mode=args.test_mode,
        version=args.version,
        filter=args.filter,
        reverse=args.reverse,
        output=output,
        image=args.image,
    )
