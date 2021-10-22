#!/bin/bash

INPUT=sg_qa
CRON_DIR="/Users/wooiliang/git/fastjobstech/fastjobs-sg/console/cron/task_qa.cron"

BASEDIR=$(dirname "$0")

perl -i.bak -pe 's/[^[:ascii:]]//g' $BASEDIR/${INPUT}_output.csv

while IFS="|" read -r search replace
do
    if [ ! -z "$search" ]; then 
        search=$(printf '%s\n' "$search" | sed -e 's/[]\/$*.^[]/\\&/g')
        replace=$(printf '%s\n' "$replace" | sed -e 's/[]\/$*.^[]/\\&/g')
        perl -pe "s/$search/$replace/" $CRON_DIR > temp.txt && mv temp.txt $CRON_DIR
    fi
done < $BASEDIR/${INPUT}_output.csv