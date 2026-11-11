#!/bin/sh
# Этап 3: граф зависимостей (BFS с рекурсией), фильтр, циклы,
# тестовый репозиторий.
cd "$(dirname "$0")/.." || exit 1

run() {
    echo "\$ ./run.sh $*"
    ./run.sh "$@"
    echo "(код возврата: $?)"
    echo
}

R=examples/repos
echo "=== Тестовый репозиторий ==="
run --package A --test-mode --repo $R/simple.txt
run --package C --test-mode --repo $R/simple.txt
run --package A --test-mode --repo $R/cycle.txt
run --package D --test-mode --repo $R/cycle.txt
run --package A --test-mode --repo $R/diamond.txt
run --package A --test-mode --repo $R/filter.txt
run --package A --test-mode --repo $R/filter.txt --filter B
run --package A --test-mode --repo $R/filter.txt --filter X
run --package A --test-mode --repo $R/broken.txt
run --package Q --test-mode --repo $R/simple.txt

echo "=== crates.io ==="
run --package serde --version 1.0.200
run --package rand --version 0.8.5
run --package rand --version 0.8.5 --filter chacha
