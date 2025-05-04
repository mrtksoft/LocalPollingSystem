#!/bin/bash

# Store data relative to the script's project location
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
DB_DIR="$SCRIPT_DIR/data"
export POLLING_DB_PATH="$DB_DIR/polling_system.db"

mkdir -p "$DB_DIR"

export FLASK_ENV=development
export FLASK_DEBUG=1

echo "Starting services..."

(cd poll_service && flask run --port 5001) &
PID1=$!
(cd vote_service && flask run --port 5002) &
PID2=$!
(cd result_service && flask run --port 5003) &
PID3=$!
echo "Services started with PIDs: $PID1, $PID2, $PID3"

wait $PID1
wait $PID2
wait $PID3
echo "Services stopped."