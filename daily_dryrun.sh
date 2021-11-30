set -ex
if cd /home/ubuntu/ledger; then
	d=`date +%Y%m%d`
	./check_day.py $d
	./check_day.py sum
#	git add ./cur/outcome_$d.json
#	git add ./cur/total.json
#	git commit -m "date $d"
#	git push origin master
fi
