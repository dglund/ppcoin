import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
from pygit2 import Repository
import requests
from flask import Flask, jsonify, request, render_template, redirect
import wallet


# Auto-creates chain.json and wallet.json if not in directory
try:
    with open('chain.json'), open('wallet.json'):
        pass
except IOError:
    with open('chain.json', 'w') as a, open('wallet.json', 'w') as b:
        a.write('')
        b.write('')


# Function for writing to chain.json
def write_json(value):
    chain_frame = {
        'Blockchain': value,
        'length': len(value),
    }
    dump = json.dumps(chain_frame, indent=2, sort_keys=True)
    with open('chain.json', 'w') as f:
        f.write(dump)


def run_wallet():
    wallet.update_wallet(node_identifier)
    if not wallet.transaction_list:
        pass
    else:
        wallet.write_wallet(node_identifier, wallet.transaction_list)
        wallet.transaction_list = []


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        with open('chain.json') as f:
            try:
                data_file = json.load(f)
                self.chain = data_file['Blockchain']
            except ValueError:
                self.new_block(previous_hash='1', proof=100)

        with open('network.json') as f:
            data = json.load(f)
        self.nodes = data['nodes']

        write_json(self.chain)

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)
        
        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/chain')

                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    # Check if the length is longer and the chain is valid
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain

            except requests.exceptions.RequestException:
                pass

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            write_json(self.chain)
            return True

        write_json(self.chain)
        return False

    def resolve_transactions(self):
        neighbours = self.nodes
        global_list = []

        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/transaction_list')
                json_response = response.json()
                for item in json_response:
                    global_list.append(item)

            except requests.exceptions.RequestException:
                pass

        blockchain.current_transactions = global_list

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain
        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof

        :param last_block: <dict> last Block
        :return: <int>
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the Proof
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.
        """

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.context_processor  # Passes Git branch name to all templates for layout reasons
def inject_version():
    return dict(version=Repository('.').head.shorthand, node=node_identifier)


@app.route('/mining', methods=['GET'])
def render_mining():
    return render_template('mining.html')


@app.route('/mine', methods=['GET'])
def mine():
    blockchain.resolve_conflicts()
    blockchain.resolve_transactions()
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    pretty = json.dumps(response, sort_keys=True, indent=2)

    write_json(blockchain.chain)
    run_wallet()

    return render_template('response.html', response=pretty)


@app.route('/transactions', methods=['GET'])
def render_transactions():

    replaced = blockchain.resolve_conflicts()
    if replaced:
        blockchain.current_transactions = []

    list_transactions = blockchain.current_transactions

    balance = wallet.wallet_balance()

    return render_template('transactions.html', context=list_transactions, wallet_balance=balance)


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        blockchain.current_transactions = []
    values = {
        'sender': node_identifier,
        'recipient': request.form['recipient'],
        'amount': int(request.form['amount'])
    }

    if int(request.form['amount']) > wallet.wallet_balance():
        response = 'Insufficient funds'
        return render_template('response.html', response=response)

    else:
        # Create a new Transaction
        index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

        response = 'Transaction will be added to Block ' + str(index)

        return render_template('response.html', response=response)


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/transaction_list', methods=['GET'])
def pending_transactions():
    response = blockchain.current_transactions

    return jsonify(response), 200


@app.route('/explorer', methods=['GET'])
def explorer():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        blockchain.current_transactions = []
    response = {
        'Blockchain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    pretty = json.dumps(response, sort_keys=True, indent=2)

    return render_template('explorer.html', value=pretty)


@app.route('/nodes')
def render_nodes():

    return render_template('nodes.html')


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    node = request.form['node_ip']

    if node is None:
        return "Error: Please supply a valid list of nodes", 400

    blockchain.register_node(node)
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    pretty = json.dumps(response, sort_keys=True, indent=2)
    return render_template('response.html', response=pretty)


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


@app.route('/wallet')
def render_wallet():
    run_wallet()

    try:
        with open('wallet.json') as f:
            data = json.load(f)
            context = json.dumps(data, indent=2, sort_keys=False)
    except ValueError:
        context = ''

    balance = wallet.wallet_balance()

    return render_template('wallet.html', wallet_data=context, wallet_balance=balance)


@app.route('/')
def render_home():
    return render_template('home.html')


@app.route('/generate')
def generate_address():
    wallet.write_wallet(node_identifier, [])
    return render_template('address.html', node=node_identifier)


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port, debug=True)
