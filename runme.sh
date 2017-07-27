#! /bin/sh

cd /home/hackspace/notdoord
while sleep 1 ; do
    echo Starting...
    ./notdoord.py /dev/ttyUSB?
    echo Exited
    sleep 1
done
