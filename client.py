"""Module to test the blockchain"""
import json
import random

import requests


def get_nodes(total_nodes: int = 3) -> list:
    """Gets a list of node domains"""

    nodes = []
    for node_index in range(total_nodes):
        node = f"localhost:{5000 + node_index}"
        nodes.append(node)

    return nodes


def display(json_data: dict) -> None:
    """Prints a formatted JSON object from a dictionary"""

    print(json.dumps(json_data, indent=2))


def get_chain(node: str) -> dict:
    """Get the chain for a given node"""

    url = f"http://{node}/chain"
    response = requests.get(url=url)
    return response.json()


def add_transaction(node: str, transaction: dict) -> dict:
    """Adds a new transaction to the blockchain"""

    url = f"http://{node}/transactions/new"
    response = requests.post(url=url, json=transaction)
    return response.json()


def get_random_transactions(node: str, total: int = 50) -> list:
    """Gets a list of random transactions and adds them to the blockchain"""

    senders = tuple(range(1, 1000))
    recipients = tuple(range(1000, 2000))

    responses = []
    for _ in range(total):
        amount_scalar = random.randint(0, 1000)
        transaction = {
            "sender": f"user{random.choice(senders)}",
            "recipient": f"user{random.choice(recipients)}",
            "amount": round(random.random() * amount_scalar, 3)
        }
        response_json = add_transaction(node, transaction)
        responses.append(response_json)

    return responses


def mine_block(node: str) -> dict:
    """Mine a new block onto the blockchain"""

    url = f"http://{node}/mine"
    response = requests.get(url=url)
    return response.json()


def register_nodes(node: str, *nodes) -> dict:
    """Add neighboring nodes into the blockchain network"""

    url = f"http://{node}/nodes/register"
    json_nodes = {"nodes": list(nodes)}
    response = requests.post(url=url, json=json_nodes)
    return response.json()


def register_all_nodes(*nodes) -> list:
    """Registers all nodes to every node"""

    responses = []
    for node in nodes:
        node_list = list(nodes)
        node_index = node_list.index(node)
        primary_node = node_list.pop(node_index)
        response_json = register_nodes(primary_node, *node_list)
        responses.append(response_json)

    return responses


def get_consensus(node: str) -> dict:
    """Runs the consensus algorithm against the node's blockchain"""

    url = f"http://{node}/nodes/resolve"
    response = requests.get(url=url)

    response_data = {}
    if response.status_code != 304:
        response_data = response.json()

    return response_data


def synchronize_blockchain_network(nodes: list) -> None:
    """Synchronize the chains for all nodes in the blockchain network"""

    synchronized = False
    while not synchronized:
        chain_sync = True

        random_chain = get_chain(random.choice(nodes))
        for node in nodes:
            get_consensus(node)
            chain = get_chain(node)
            if random_chain != chain:
                mine_block(node)
                chain_sync = False

        if chain_sync:
            synchronized = True


def run_simulation(nodes: list, total_tests: int = 10, sync: int = 1) -> None:
    """Simulates an active blockchain network"""

    for test_index in range(total_tests):
        print(f"Test: {test_index + 1}", end="\r")
        node = random.choice(nodes)
        get_random_transactions(node)
        mine_block(node)
        if not test_index % sync:
            synchronize_blockchain_network(nodes)
        print()


def main():
    """Runs the main process"""

    nodes = get_nodes()
    register_all_nodes(*nodes)
    run_simulation(nodes, total_tests=500, sync=50)
    synchronize_blockchain_network(nodes)


if __name__ == "__main__":
    main()
