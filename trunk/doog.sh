#!/bin/sh
cd .
export LD_LIBRARY_PATH=.

trap 'echo "Stopping DoogRadio server..."; sleep 1; exit 0' 2

echo "Starting DoogRadio server...  Press CTRL+C to stop"

while true
do
	python radio.py
	sleep 10
done



