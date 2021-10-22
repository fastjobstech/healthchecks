#!/bin/bash

INPUT=sg_qa
API_HOST=hc-dev.fastjobs.sg
API_KEY=

BASEDIR=$(dirname "$0")

output=$(curl --header "X-Api-Key: $API_KEY" https://$API_HOST/api/v1/checks/ | jq .checks)

perl -i.bak -pe 's/[^[:ascii:]]//g' $BASEDIR/$INPUT.csv

while IFS="|" read -r name description cron
do
    is_exist=false
    if [[ $name = *[![:ascii:]]* ]]; then
        echo "Contain Non-ASCII"
        exit
    fi
    for row in $(echo "${output}" | jq -r '.[] | @base64'); do
        _jq() {
            echo ${row} | base64 --decode | jq -r ${1}
        }
        if [ "$name" == "$(_jq '.name')" ]; then
            is_exist=true
            break
        fi
    done
    if [ "$is_exist" == false ]; then
        JSON_STRING=$( jq -n \
            --arg name "$name" \
            --arg description "$description" \
            --arg cron "${cron/$'\r'/}" \
            '{name: $name, desc: $description, grace: 300, schedule: $cron, tz: "Asia/Singapore"}' )
        pingurl=$(curl https://$API_HOST/api/v1/checks/ \
            --header "X-Api-Key: $API_KEY" \
            --data "$JSON_STRING" | jq -r .ping_url)
        echo "$description|$description && curl -fsS -m 10 --retry 5 -o /dev/null $pingurl" >> $BASEDIR/${INPUT}_output.csv
    fi
done < $BASEDIR/$INPUT.csv