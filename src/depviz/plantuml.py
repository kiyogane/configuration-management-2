"""Текстовое представление графа на PlantUML и вывод изображения."""

import os
import shutil
import subprocess
import sys
import webbrowser
import zlib

SERVER = "https://www.plantuml.com/plantuml"
ALPHABET = ("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz-_")
SIX_BITS = 0x3F
GROUP = 3
ROOT_COLOR = "#LightBlue"


def node_ids(graph):
    """Сопоставить вершинам короткие идентификаторы n0, n1, ..."""
    ids = {}
    for node, deps in graph.items():
        for item in [node] + deps:
            ids.setdefault(item, f"n{len(ids)}")
    return ids


def to_plantuml(graph, root, reverse=False):
    """Сформировать описание графа на языке PlantUML.

    Ребро ведет от пакета к его зависимости; в режиме обратных
    зависимостей — от зависящего пакета к анализируемому.
    """
    ids = node_ids(graph)
    kind = "Обратные зависимости" if reverse else "Зависимости"
    lines = ["@startuml", f"title {kind} {root.label()}",
             "skinparam defaultTextAlignment center"]
    for node, short in ids.items():
        color = f" {ROOT_COLOR}" if node == root else ""
        lines.append(f'rectangle "{node.label()}" as {short}{color}')
    for node, deps in graph.items():
        for dep in deps:
            pair = (ids[dep], ids[node]) if reverse else (ids[node], ids[dep])
            lines.append(f"{pair[0]} --> {pair[1]}")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def encode(text):
    """Закодировать текст для URL сервера PlantUML (deflate + base64)."""
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    data = compressor.compress(text.encode("utf-8")) + compressor.flush()
    result = []
    for start in range(0, len(data), GROUP):
        chunk = data[start:start + GROUP].ljust(GROUP, b"\0")
        number = int.from_bytes(chunk, "big")
        for shift in (18, 12, 6, 0):
            result.append(ALPHABET[(number >> shift) & SIX_BITS])
    return "".join(result)


def server_url(text, image_format="png"):
    """URL картинки на публичном сервере PlantUML."""
    return f"{SERVER}/{image_format}/{encode(text)}"


def open_file(path):
    """Открыть файл программой просмотра по умолчанию."""
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
    elif shutil.which("xdg-open"):
        subprocess.run(["xdg-open", path], check=False)


def local_command(puml_path):
    """Команда локального PlantUML (plantuml или java -jar) или None."""
    if shutil.which("plantuml"):
        return ["plantuml", "-tpng", puml_path]
    jar = os.environ.get("PLANTUML_JAR")
    if jar and shutil.which("java"):
        return ["java", "-jar", jar, "-tpng", puml_path]
    return None


def show_image(puml_path, text):
    """Вывести изображение: локальный PlantUML или веб-сервер."""
    command = local_command(puml_path)
    if command:
        subprocess.run(command, check=True)
        png = os.path.splitext(puml_path)[0] + ".png"
        print(f"Изображение: {png}")
        open_file(png)
        return
    url = server_url(text)
    print(f"Локальный PlantUML не найден, изображение: {url}")
    webbrowser.open(url)
