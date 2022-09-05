"""Module to create a node in a blockchain network"""
from uuid import uuid4

from flask import Flask, jsonify, request

from blockchain import Blockchain


# Create API server instance for this blockchain node
app = Flask(__name__)

# Generate a globally unique address for this node
node_id = str(uuid4()).replace("-", "")

# Create an instance of the blockchain
blockchain = Blockchain()


@app.route("/mine")
def mine():
    """Mine a new block into the blockchain"""

    # Run the proof of work algorithm to get the next proof
    proof = blockchain.proof_of_work()

    # There must be a reward for evaluating the proof of work algorithm
    # A new block being mined is denoted by the sender being set to zero
    blockchain.new_transaction(
        sender="0",
        recipient=node_id,
        amount=1.0,
    )

    # Mine the new block into the blockchain by adding it to the chain
    previous_hash = blockchain.hash(blockchain.last_block)
    block = blockchain.new_block(proof, previous_hash=previous_hash)

    response_json = {
        "message": "Mined New Block",
        "index": block["index"],
        "transactions": block["transactions"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"]
    }

    return jsonify(response_json), 200


@app.route("/transactions/new", methods=["POST"])
def new_transaction():
    """Add a new transaction to the blockchain"""

    try:
        sender = request.json["sender"]
        recipient = request.json["recipient"]
        amount = request.json["amount"]
    except KeyError:
        return "Missing required values", 400
    else:
        transaction = (sender, recipient, amount)

    # Add the new transaction to the blockchain
    block_index = blockchain.new_transaction(*transaction)

    transaction_msg = f"New transaction added to block: {block_index}"
    response_json = {"message": transaction_msg}

    return jsonify(response_json), 201


@app.route("/chain")
def full_chain():
    """Get the full chain for this node's blockchain"""

    response = {
        "chain": blockchain.chain,
        "length": len(blockchain.chain),
    }

    return jsonify(response), 200


@app.route("/nodes/register", methods=["POST"])
def register_nodes():
    """Registers new nodes into the blockchain network"""

    try:
        nodes = request.json["nodes"]
    except KeyError:
        return "Invalid list of nodes provided", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        "message": "Added new nodes to the blockchain network",
        "total_nodes": list(blockchain.nodes),
    }

    return jsonify(response), 201


@app.route("/nodes/resolve")
def consensus():
    """Consensus validation to resolve blockchain node's chain conflicts"""

    chain_replaced = blockchain.resolve_conflicts()

    if chain_replaced:
        response = {
            "message": "Chain has been replaced",
            "new_chain": blockchain.chain
        }
        status_code = 200
    else:
        response = {
            "message": "This chain is the authoritative",
            "chain": blockchain.chain
        }
        status_code = 304

    return jsonify(response), status_code


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-p", "--port", default=5000, type=int,
                        help="specify the web server listening port")
    args = parser.parse_args()

    app.run(host="127.0.0.1", port=args.port)
