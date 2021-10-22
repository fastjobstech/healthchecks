# How to use the script

## Run create_checks.sh
1. Get cron details from `console/cron/task.cron`
2. Form the csv using this format. The last line of the file must be empty (Can [delimiter converter](https://onlinecsvtools.com/change-csv-delimiter) to convert from comma to pipe symbol)

`check name|check description (copy the whole line of cron)|cron schedule`

`/usr/local/bin/php /app/yii interview expire|0 4 * * * /usr/local/bin/php /app/yii interview expire|0 4 * * *`

3. Fill in `INPUT=`, `API_HOST=` and `API_KEY=`
4. `script/create_checks.sh` to run the script
5. Output will be generated

## Run populate_url.sh
1. Fill in `INPUT=` and `CRON_DIR=`
2. `script/populate_url.sh` to run the script
3. `console/cron/task.cron` should be updated.
4. Commit the `task.cron`