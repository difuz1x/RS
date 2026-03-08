#!/bin/bash

DIR="/home/difuzix/Загальне/Розподілені системи/RS/PR5"


tmux kill-session -t smarthome 2>/dev/null

cd "$DIR" || exit


source .venv/bin/activate
docker-compose down