"""Module containing a basic blockchain"""
import hashlib
import json
from time import time
from urllib.parse import urlparse

import requests


class Blockchain:
    """Class representing a blockchain"""

    def __init__(self):
        self.chain = []
        self.transactions = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash="1", proof=1)

    def register_node(self, node_address: str) -> None:
        """
        Registers a new node to the set of known nodes

        This function registers a new node to the set of known nodes by
        the blockchain.  The node web address is passed in and as long
        as the address is a valid address, it is added to the set.

        """

        parsed_url = urlparse(node_address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts a URL without a scheme like "127.0.0.1:5000"
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError(f"Invalid URL provided: {node_address}")

    def valid_chain(self, chain: dict) -> bool:
        """
        Determines whether a given blockchain is valid or not

        The valid chain method is used to check whether a provided blockchain
        is actually valid or not.  A blockchain's chain dictionary is passed
        in and validated for integrity.  The validation happens by checking
        each individual block in the chain for integrity.  Each block is
        rehashed and that hash is then compared against the next block's
        previous_hash field.  Assuming the hashes are correct, the next step
        to validate each block is to verify that the proof of work is correct.
        If every block in the chain is determined to be valid then the function
        will return True.

        """

        # Set the first block in chain and second block's index
        last_block = chain[0]
        current_index = 1

        is_valid = True
        while current_index < len(chain):
            block = chain[current_index]

            # Verify the previous hash is correct
            last_block_hash = self.hash(last_block)
            if block["previous_hash"] != last_block_hash:
                is_valid = False
                break

            # Check that the Proof of Work is correct
            last_proof = last_block["proof"]
            proof = block["proof"]
            if not self.valid_proof(last_proof, proof, last_block_hash):
                is_valid = False
                break

            last_block = block
            current_index += 1

        return is_valid

    def resolve_conflicts(self) -> bool:
        """
        Consensus algorithm for updating blockchain

        This is the consensus algorithm, it resolves conflicts by replacing
        this blockchain's chain with the longest chain in the network.  Each
        known node's chain in the network is checked after a GET request is
        sent out.  Each node's chain is then checked to determine whether
        that chain is longer than this blockchain's chain.  Each node's chain
        is also checked for validity as well.  If a node in the network is
        discovered to be longer than this blockchain's chain and that node's
        chain is valid, then this blockchain's chain is replaced with the
        chain of that node.  If this blockchain's chain was replaced, then
        the function will return True.

        """

        new_chain = None
        max_length = len(self.chain)

        # GET and validate every chain in the blockchain network
        chain_replaced = False
        for node in self.nodes:
            node_chain_url = f"http://{node}/chain"
            response = requests.get(node_chain_url)

            if response.status_code in (200, 304):
                node_json = response.json()
                node_length = node_json["length"]
                node_chain = node_json["chain"]

                # Check if the length is longer and the chain is valid
                is_longer = node_length > max_length
                is_valid = self.valid_chain(node_chain)
                if is_longer and is_valid:
                    max_length = node_length
                    new_chain = node_chain

        # Replace this chain if a new chain is valid and longer
        if new_chain:
            self.chain = new_chain
            chain_replaced = True

        return chain_replaced

    def new_block(self, proof: str, previous_hash: str = None) -> dict:
        """
        Adds a new block to the chain

        A new block is created using the calculated proof and the hash
        of the previous block in the chain.  The new block will contain
        an index, which is calculated by the length of the current chain
        plus one.  The new block will have a UNIX timestamp of the current
        time.  The new block contains the proof that was solved for the
        new block.  The new block will also contain the hash of the previous
        block.  If the previous hash is not provided, the last block in the
        chain will be hashed automatically.  The pending transactions are
        cleared and the new block is added to the chain.  The new block is
        then returned to the calling function.

        """

        block = {
            "index": len(self.chain) + 1,
            "timestamp": time() if len(self.chain) else 0,
            "transactions": self.transactions,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.last_block)
        }

        # Resets the current list of pending transactions
        self.transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self,
                        sender: str,
                        recipient: str,
                        amount: float
                        ) -> int:
        """
        Adds a new transaction to the existing transactions

        Creates a new transaction that will be sent to the next
        block in the chain.  There are three required fields that
        a transaction must include.  The 'sender', 'recipient', and
        'amount' are required fields needed to create a new
        transaction.  The index of the next block that will be mined
        in the chain is then returned.

        """

        self.transactions.append({
            "sender": sender,
            "recipient": recipient,
            "amount": amount
        })

        return self.last_block["index"] + 1

    @property
    def last_block(self):
        """The last block in the chain"""

        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Generates a hash for a given block

        The hash function creates a SHA256 block hash of the given block
        and ensures that the dictionary is sorted before hashing.

        """

        block_str = json.dumps(block, sort_keys=True).encode("utf8")
        return hashlib.sha256(block_str).hexdigest()

    def proof_of_work(self) -> str:
        """
        Basic proof of work algorithm

        This function is used to calculate proof of work when mining a
        new block.  The proof of work function compares the current proof
        value against the last proof value as well as the last block's hash.
        When the proof of work is satisfied, the proof is returned to the
        calling function.

        """

        last_proof = self.last_block["proof"]
        last_hash = self.hash(self.last_block)

        proof = 0
        while not self.valid_proof(last_proof, proof, last_hash):
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int, last_hash: str) -> bool:
        """
        Validates proof for a new block

        Validates the new block proof using the current proof attempt, the
        last block's proof, and the last block's actual recomputed hash.
        The last proof, the current proof, and the last hash are concatenated
        together.  A SHA256 hash of the concatenated string is calculated.
        If the first four characters of the hash are all zeroes, then the
        proof is considered valid.

        """

        guess = f"{last_proof}{proof}{last_hash}".encode("utf8")
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
