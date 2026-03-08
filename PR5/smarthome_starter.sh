#!/bin/bash

DIR="/home/difuzix/Загальне/Розподілені системи/RS/PR5"
PYTHON_BIN="$DIR/.venv/bin/python"

sudo systemctl start docker

cd "$DIR" || exit

source .venv/bin/activate
docker-compose up -d
sleep 3

tmux new-session -d -s smarthome -n subscriber
tmux send-keys -t smarthome "cd '$DIR'; '$PYTHON_BIN' devices/subscriber.py" Enter

tmux new-window -t smarthome -n hub
tmux send-keys -t smarthome "cd '$DIR'; '$PYTHON_BIN' smart_hub.py" Enter

tmux new-window -t smarthome -n publisher
tmux send-keys -t smarthome "cd '$DIR'; '$PYTHON_BIN' sensors/publisher.py" Enter

tmux new-window -t smarthome -n dashboard
tmux send-keys -t smarthome "cd '$DIR'; '$PYTHON_BIN' dashboard.py" Enter

tmux attach -t smarthome