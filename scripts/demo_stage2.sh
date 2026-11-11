#!/bin/sh
# Этап 2: прямые зависимости заданной версии пакета из crates.io.
cd "$(dirname "$0")/.." || exit 1

run() {
    echo "\$ ./run.sh $*"
    ./run.sh "$@"
    echo "(код возврата: $?)"
    echo
}

run --package serde --version 1.0.200
run --package rand --version 0.8.5
run --package tokio --version 1.40.0

echo "=== Ошибки репозитория ==="
run --package nosuchcrate-xyz --version 1.0.0
run --package serde --version 7.7.7
run --package serde --version 1.0.200 --repo https://no-such-host.invalid
