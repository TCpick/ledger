#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import logging
import re
import os
import sys

def main():
    filename = sys.argv[1]
    with open(filename, "r") as f_input:
        data = json.load(f_input)
        f_input.close()
        f_out = open(filename, "w")
        json.dump(data,f_out,indent = 2)


################## main ####################

if __name__ == "__main__":
    main()
