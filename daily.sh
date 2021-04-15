set -ex
if cd /home/pick/mine/ledger; then
	d=`date +%Y%m%d`
	./check_day.py $d
	./check_day.py sum
	git add outcome_$d.json
	git add total.json
	git commit -m "date $d"
	git push origin master
fi
