#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import logging
import re
import os
import sys
from http import HTTPStatus


def getInfo(user):
    url = "https://api.f2pool.com/ethereum/%s" %(user)
    r = requests.get(url)
    for i in range(10):
        if r.status_code == HTTPStatus.OK:
            info = json.loads(r.text)        
            return info
        else:
            logging.warning('get pool info fail, retrying...') 
            sleep(5)
    logging.error('fail to get pool info from %s, retry time exceed.' %url) 

def calOutcome(info):
    totalOutcome = info['ori_value_last_day']
    totalHashes = info['ori_hashes_last_day']
    workersOutcome = {}
    workersHashesCheck = 0
    for worker in info['workers']:
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

def saveOrigin(dateStr, data):
    with open('./ori/%s.json' %dateStr, 'w') as oriOut:
        json.dump(data, oriOut)
        logging.info("Original data saved to ori/%s.json" %dateStr)

def saveOutcome(dateStr, data):
    with open('./outcome_%s.json' %dateStr, 'w') as outFile:
        json.dump(data, outFile)
        logging.info("todays outcome calculate done. see outcome_%s.json" %dateStr)

def saveTotal(data):
    with open('./total.json' ,'w') as outFile:
        json.dump(data, outFile)
        logging.info("total outcome calculate done. see total.json")

def sumAll():
    total_ledger = {}
    for f in os.listdir():
        if f.startswith("outcome"):
            dateStr = re.split("[._]", f)[-2]
            with open('./outcome_%s.json' %dateStr, 'r') as outcome:
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
        saveTotal(total)
    else:
        logfileName = './log/%s.log' %dateStr
        logging.basicConfig(filename=logfileName, level=logging.DEBUG)
        info = getInfo('tcpick')
        saveOrigin(dateStr, info)
        out = calOutcome(info)
        out = sumDaily(out)
        saveOutcome(dateStr, out)


################## main ####################

if __name__ == "__main__":
    main()
