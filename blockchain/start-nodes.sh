#!/bin/bash

python3.6 -m venv venv
source venv/bin/actvate
pip install -r requirements.txt
python node.py -p 5000 2>&1 >logs/node1.log &
python node.py -p 5001 2>&1 >logs/node2.log &
python node.py -p 5002 2>&1 >logs/node3.log &
tail -f /dev/null
