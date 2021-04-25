#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import logging
import re
import os
import sys
import time
from http import HTTPStatus

CUR_DIR = "./cur/"
RETRY_TIME = 10
ETH_ADDR = "0xf83fb33e94D1c6dc1c7325E95dDE4716F020277c"

def restGet(url):
    for i in range(RETRY_TIME):
        r = requests.get(url)
        if r.status_code == HTTPStatus.OK:
            return json.loads(r.text)
        else:
            logging.warning('get from %s fail, retrying...' %url) 
            sleep(5)
    logging.error('Fail to get from %s, retry time exceed.' %url) 
    return None

def getWorkerDict_em(miner):
    url = "https://api.ethermine.org/miner/%s/dashboard" %miner
    rsp = restGet(url)
    res = {}
    if "data" in rsp:
        if "workers" in rsp["data"]:
            for item in rsp["data"]["workers"]:
                res[item["worker"]] = {}
    return res

def getWorkerHistory_em(miner, worker):
    url = "https://api.ethermine.org/miner/%s/worker/%s/history" %(miner, worker)
    rsp = restGet(url)
    if "data" in rsp:
        return rsp["data"]
    return None

def calWorkerShare_em(history):
    timestamp = int(time.time())
    valid, stale, reject = 0,0,0
    k = 0
    for i in range(1, len(history) + 1):
        if k == 0:
            item = history[-i]
            if item["time"] > timestamp - 86400:
                valid += item["validShares"]
                stale += item["staleShares"]
                reject += item["invalidShares"]
        k = (k + 1) % 6
    return {"valid": valid, "stale": stale, "reject": reject}

def calWorker_em(workers, daily_total):
    total_valid = 0
    for w in workers:
        total_valid += workers[w]["valid"]
    for w in workers:
        workers[w]["portion"] = workers[w]["valid"] / total_valid
        workers[w]["outcome"] = workers[w]["portion"] * daily_total
        workers[w]["stale_rate"] = workers[w]["stale"] / workers[w]["valid"]
        workers[w]["reject_rate"] = workers[w]["reject"] / workers[w]["valid"]

def getDailyOutcome_em(miner):
    url = "https://api.ethermine.org/miner/%s/currentStats" %miner
    rsp = restGet(url)
    if "data" in rsp:
        if "coinsPerMin" in rsp["data"]:
            return rsp["data"]["coinsPerMin"] * 60 * 24
    return 0

def ethermine_cal(dateStr, miner, out):
    daily_total = getDailyOutcome_em(miner)
    workers = getWorkerDict_em(miner)
    for w in workers:
        workers[w] = calWorkerShare_em(getWorkerHistory_em(miner, w))
    calWorker_em(workers, daily_total)

    ethermine_daily = {"Total": daily_total, "workers": workers}
    saveOrigin("ethermine" + dateStr, ethermine_daily)

    for w in workers:
        if w in out:
            out[w] += workers[w]["outcome"]
        else:
            out[w] = workers[w]["outcome"]
    return out

def getInfo_f2(user):
    url = "https://api.f2pool.com/ethereum/%s" %(user)
    return restGet(url)

def calOutcome_f2(info, outcome):
    totalOutcome = info['ori_value_last_day']
    totalHashes = info['ori_hashes_last_day']
    workersOutcome = outcome
    workersHashesCheck = 0
    for worker in info['workers']:
        if not worker[0] in workersOutcome:
            workersOutcome[worker[0]] = 0
        workersOutcome[worker[0]] = totalOutcome * worker[4] / totalHashes 
        workersHashesCheck += worker[4]
    if workersHashesCheck != totalHashes:
        logging.error('Total hashes check mismatch! ori: %d, workers %d, rate %f'\
                      %(totalHashes, workersHashesCheck, \
                        workersHashesCheck/totalHashes))
    return workersOutcome

def sumDaily(workersOutcome):
    if "workers" in workersOutcome:
        if type(workersOutcome["workers"]) == type({}):
            return workersOutcome
    else:
        out = {}
        out["workers"] = workersOutcome
        sumd = 0
        for worker in workersOutcome:
            sumd += workersOutcome[worker]
        out["sum"] = sumd
        return out

def f2pool_cal(dateStr, out):
        f2_info = getInfo_f2('tcpick')
        saveOrigin("f2pool" + dateStr, f2_info)
        return calOutcome_f2(f2_info, out)

def saveOrigin(dateStr, data):
    with open('./ori/%s.json' %dateStr, 'w') as oriOut:
        json.dump(data, oriOut, indent = 4)
        logging.info("Original data saved to ori/%s.json" %dateStr)

def saveOutcome(dateStr, data):
    with open(CUR_DIR + './outcome_%s.json' %dateStr, 'w') as outFile:
        json.dump(data, outFile, indent = 4)
        logging.info("todays outcome calculate done. see outcome_%s.json" %dateStr)

def saveTotal(data):
    with open(CUR_DIR + './total.json' ,'w') as outFile:
        json.dump(data, outFile, indent = 4)
        logging.info("total outcome calculate done. see total.json")

def calPortion(total_ledger):
    s = 0
    for w in total_ledger:
        s += total_ledger[w]
    r = {}
    r["sum"] = s
    r["coin"] = total_ledger
    r["portion"] = {}
    for w in total_ledger:
        r["portion"][w] = total_ledger[w] / s
    return r

def sumAll():
    total_ledger = {}
    for f in os.listdir(CUR_DIR):
        if f.startswith("outcome"):
            dateStr = re.split("[._]", f)[-2]
            with open(CUR_DIR + './outcome_%s.json' %dateStr, 'r') as outcome:
                out = json.load(outcome)
                out = sumDaily(out)
                saveOutcome(dateStr, out)
                for w in out["workers"]:
                    if w in total_ledger:
                        total_ledger[w] += out["workers"][w]
                    else:
                        total_ledger[w] =  out["workers"][w]
    logging.info("total ledger content %s" %total_ledger)
    return total_ledger

def main():
    dateStr = sys.argv[1]
    if dateStr == "sum":
        total = sumAll()
        total_w_portion = calPortion(total)
        saveTotal(total_w_portion)
    else:
        logfileName = './log/%s.log' %dateStr
        logging.basicConfig(filename=logfileName, level=logging.DEBUG)
        out = {}
        out = f2pool_cal(dateStr, out)
        out = ethermine_cal(dateStr, ETH_ADDR, out)
        out = sumDaily(out)
        saveOutcome(dateStr, out)


################## main ####################

if __name__ == "__main__":
    main()
