set -ex
if cd /home/pick/mine/ledger; then
	d=`date +%Y%m%d`
	./check_day.py $d
	./check_day.py sum
	git add ./cur/outcome_${d}AM.json
	git add ./cur/outcome_${d}PM.json
	git add ./cur/total.json
	git commit -m "date $d"
	git push origin master
fi
