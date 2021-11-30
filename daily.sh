set -ex
if cd /home/ubuntu/ledger; then
	d=`date +%Y%m%d`
	./check_day.py $d
	./check_day.py sum
	#git add --ignore-errors ./cur/outcome_${d}AM.json 
	#git add --ignore-errors ./cur/outcome_${d}PM.json 
	#git add ./cur/total.json
	git add --all
	git commit -m "date $d"
	git push origin master
fi
