#!/bin/bash
cat $* | /usr/bin/pyzor report > /dev/null 2>&1
/usr/bin/razor-report -f $* > /dev/null 2>&1
/usr/bin/sa-learn --spam $* > /dev/null 2>&1
exit 0
