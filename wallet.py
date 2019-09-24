import json


#wallet_id = '39cf594f034b4fa982c18cbf72755cba'


def write_wallet(wallet_id, transaction_data):
    frame = {wallet_id: transaction_data}
    dump = json.dumps(frame, indent=2, sort_keys=True)
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


#update_wallet()
#frame = {wallet_id: transaction_list}
#write_wallet(frame)