#!/bin/bash

if [[ -f ".venv/bin/python" ]]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python"
fi

SERVER=$1
CLIENT=$2


if [[ -z "$SERVER" && -z "$CLIENT" ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]];  then

    echo -e "The usage of this utility is: \n\n lab_start \t <server> \t <client> \n\n\t\t or \n\n $0 \t <server> \t <client>"
    exit 0
fi 

if [[ -n "$SERVER" ]]; then

    $PYTHON  $SERVER &
    echo "Server started with PID $!"

fi
sleep 2 

if [[ -n "$CLIENT" ]]; then

    $PYTHON $CLIENT 
    echo "Client started with PID $!"

fi 