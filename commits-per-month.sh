#!/bin/sh
bzr log --short --forward | sed -n -e 's/.*\([0-9]\{4\}-[0-9]\{2\}\).*/\1/p' | uniq -c | sed -n -e 's/\ *\(.*\)\ \(.*\)/\2\,\1/p'
