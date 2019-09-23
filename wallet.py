from uuid import uuid4
import json

class Wallet:
    id = '860300418ae842b9842224be812d8883'
    #id = str(uuid4()).replace('-', '')
    transaction = {
        'sender': '',
        'recipient': '',
        'amount': '',
        'block_no': ''
    }


def write_wallet(wallet_data):
    dump = json.dumps(wallet_data, indent=2, sort_keys=True)
    with open('wallet.json', 'w') as f:
        f.write(dump)


transaction_list = []


def wallet_entry(sender, recipient, amount, block_no):
    entry = {
        'sender': sender,
        'recipient': recipient,
        'amount': amount,
        'block_no': block_no
    }

    transaction_list.append(entry)


def update_wallet():
    with open('chain.json') as f:
        data = json.load(f)
        chain = data['Blockchain']
    for block in chain:
        block_no = (block['index'])
        transactions = block['transactions']
        for transaction in transactions:
            if transaction['recipient'] or transaction['sender'] == Wallet.id:

                wallet_entry(
                    transaction['sender'],
                    transaction['recipient'],
                    transaction['amount'],
                    block_no
                )


update_wallet()
frame = {Wallet.id: transaction_list}
write_wallet(frame)