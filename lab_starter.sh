#!/bin/bash

source ./.venv/bin/activate

PYTHON=".venv/bin/python"

SERVER=$1
CLIENT=$2
CLIENT_AMOUNT=${3:-1}

if [[ -z "$SERVER" && -z "$CLIENT" ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo -e "The usage of this utility is: \n\n lab_start \t <server> \t <client> \t <client_amount> \n\n\t\t or \n\n $0 \t <server> \t <client> \t <client_amount>"
    exit 0
fi

LOG_FILE="/home/difuzix/Загальне/Розподілені системи/RS/lab_starter.log"> "$LOG_FILE"

konsole -e bash -c "tail -f '$LOG_FILE'; exec bash" & KONSOLE_PID=$!
echo "Konsole log file started with PID $KONSOLE_PID" >> "$LOG_FILE"



if [[ -n "$SERVER" ]]; then
    $PYTHON $SERVER & SERVER_PID=$!
    echo "Server started with PID $SERVER_PID" >> "$LOG_FILE"
fi

sleep 2
AUTH_PID=$(pgrep -f "auth_server.py")

shutdown_all() {

    echo "Shutting down server with PID $SERVER_PID" >> "$LOG_FILE"
    kill $SERVER_PID 2>/dev/null

    if [[ -n "$AUTH_PID" ]]; then
        kill $AUTH_PID 2>/dev/null
        echo "Auth server with PID $AUTH_PID killed" >> "$LOG_FILE"
    fi

    echo "Konsole log file stopped with PID $KONSOLE_PID" >> "$LOG_FILE"
    sleep 1
    kill $KONSOLE_PID 2>/dev/null
    
}

if [[ -n "$CLIENT" ]]; then
    client_pids=()
    for i in $(seq 1 $CLIENT_AMOUNT); do
        $PYTHON $CLIENT & client_pid=$!
        client_pids+=($client_pid)
        echo "Client $i started with PID $client_pid" >> "$LOG_FILE"
    done

    for client_pid in "${client_pids[@]}"; do
        wait $client_pid
        echo "Client $client_pid finished" >> "$LOG_FILE"
    done

    shutdown_all
else
    echo "No client specified, exiting" >> "$LOG_FILE"
    shutdown_all
fi