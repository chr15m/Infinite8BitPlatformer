#!/bin/sh

ids=""
for i in `seq 20`
do
	python I8BPTestClient.py &
	ids="$ids $!"
	sleep 1
done
sleep 5
kill $ids
