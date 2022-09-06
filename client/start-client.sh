#!/bin/bash

python3.6 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
NODES="blockchain:5000,blockchain:5001,blockchain:5002"
echo "Waiting 10 seconds for blockchain network to come online..."
sleep 10  # wait ten seconds for the blockchain to instantiate
echo "Executing simulated client traffic"
python client.py -n $NODES 2>&1 >logs/client.log &
tail -f /dev/null
