#!/bin/sh
# Этап 4: обратные зависимости (тот же обход BFS по обращенному графу).
cd "$(dirname "$0")/.." || exit 1

run() {
    echo "\$ ./run.sh $*"
    ./run.sh "$@"
    echo "(код возврата: $?)"
    echo
}

R=examples/repos
run --package D --test-mode --repo $R/simple.txt --reverse
run --package E --test-mode --repo $R/simple.txt --reverse
run --package A --test-mode --repo $R/simple.txt --reverse
run --package A --test-mode --repo $R/cycle.txt --reverse
run --package D --test-mode --repo $R/cycle.txt --reverse
run --package Z --test-mode --repo $R/diamond.txt --reverse
run --package XD --test-mode --repo $R/filter.txt --reverse
run --package XD --test-mode --repo $R/filter.txt --reverse --filter C
run --package Q --test-mode --repo $R/simple.txt --reverse
run --package serde --version 1.0.200 --reverse
