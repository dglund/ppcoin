from uuid import uuid4
import json

class Wallet:

    id = str(uuid4()).replace('-', '')
    transaction = {
        'sender': '',
        'recipient': '',
        'amount': '',
        'block_no': ''
    }

wallet_data = {
        Wallet.id: Wallet.transaction,
    }

def write_wallet(wallet_data):
    dump = json.dumps(wallet_data, indent=2, sort_keys=True)
    with open('wallet.json', 'w') as f:
        f.write(dump)

# Pseudo-code
def wallet_entry(sender, recipient, amount, block_no):
    entry = {
        'sender': sender,
        'recipient': recipient,
        'amount': amount,
        'block_no': block_no
    }

    return entry

transactions = []

for block in chain.json:
    if sender or recipient == Wallet.id:
        transactions.append(wallet_entry(sender, recipient, amount, block_no))

write_wallet(transactions)