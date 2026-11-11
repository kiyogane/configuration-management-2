#!/bin/sh
# Запуск всех демонстрационных скриптов по порядку.
cd "$(dirname "$0")" || exit 1
for script in demo_stage*.sh; do
    echo "########## $script ##########"
    sh "$script"
done
