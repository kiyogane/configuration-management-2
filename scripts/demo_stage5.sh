#!/bin/sh
# Этап 5: PlantUML-представление и изображение графа для трех пакетов.
# Для локальной отрисовки нужен plantuml в PATH или переменная
# PLANTUML_JAR=/путь/plantuml.jar; иначе откроется сервер plantuml.com.
cd "$(dirname "$0")/.." || exit 1

run() {
    echo "\$ ./run.sh $*"
    ./run.sh "$@"
    echo "(код возврата: $?)"
    echo
}

run --package serde --version 1.0.200 --image
run --package rand --version 0.8.5 --image
run --package tokio --version 1.40.0 --image
run --package A --test-mode --repo examples/repos/cycle.txt --image
run --package D --test-mode --repo examples/repos/simple.txt --reverse --image

echo "=== Ошибки ==="
run --package serde --version 1.0.200 --output graph.png
