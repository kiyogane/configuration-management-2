#!/bin/sh
# Этап 1: вывод параметров и обработка ошибок для каждого параметра.
cd "$(dirname "$0")/.." || exit 1

run() {
    echo "\$ ./run.sh $*"
    ./run.sh "$@"
    echo "(код возврата: $?)"
    echo
}

echo "=== Корректный запуск ==="
run --package serde --version 1.0.200 --filter derive

echo "=== Ошибки ==="
run --version 1.0.200
run --package "bad name!" --version 1.0.200
run --package serde
run --package serde --version 1.x
run --package serde --version 1.0.200 --repo ftp:/example
run --package a --test-mode --repo README.md
run --package A --test-mode --repo /no/such/file.txt
run --package serde --version 1.0.200 --filter ser
run --package serde --version 1.0.200 --filter " x"
