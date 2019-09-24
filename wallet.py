import json


transaction_list = []


def write_wallet(wallet_id, transaction_data):
    try:
        with open('wallet.json') as f:
            data = json.load(f)
            data[wallet_id] = transaction_data
            dump = json.dumps(data, indent=2, sort_keys=False)
            with open('wallet.json', 'w') as f:
                f.write(dump)
    except ValueError:
        data = {wallet_id: transaction_data}
        dump = json.dumps(data, indent=2, sort_keys=False)
        with open('wallet.json', 'w') as f:
            f.write(dump)


def wallet_entry(sender, recipient, amount, block_no):

    entry = {
        'sender': sender,
        'recipient': recipient,
        'amount': amount,
        'block_no': block_no
    }

    transaction_list.append(entry)


def update_wallet(wallet_id):
    with open('chain.json') as f:
        data = json.load(f)
        chain = data['Blockchain']
    for block in chain:
        block_no = (block['index'])
        transactions = block['transactions']
        for transaction in transactions:
            if transaction['recipient'] == wallet_id or transaction['sender'] == wallet_id:

                wallet_entry(
                    transaction['sender'],
                    transaction['recipient'],
                    transaction['amount'],
                    block_no
                )
