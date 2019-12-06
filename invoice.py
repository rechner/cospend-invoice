#!/usr/bin/env python3
import sys
import csv
from decimal import Decimal
import requests
from flask import Flask, render_template

app = Flask(__name__)

API_URL = "https://cloud.knot.space/apps/cospend/api/projects/project/password"

TWOPLACES = Decimal(10) ** -2
CATEGORIES = {
    -1 : 'Groceries',
    -2 : 'Leisure',
    -3 : 'Rent',
    -4 : 'Bills',
    -5 : 'Culture',
    -6 : 'Health',
    -7 : 'Tools',
    -8 : 'Multimedia',
    -9 : 'Clothes',
}

PAYMENT_MODES = {
    'c' : 'Credit Card',
    'b' : 'Cash',
    'f' : 'Check',
}

def get_members(api_url=API_URL):
    api_response = requests.get(api_url).json()
    parsed_members = {}
    for member in api_response['members']:
        parsed_members[member['id']] = member

    return parsed_members


def get_active_members(members):
    return [ members[idx] for idx in members if members[idx]['activated'] ]


#if len(sys.argv) != 2:
#    print("Usage: {0} file.csv".format(sys.argv[0]))
#    exit(1)

def parse_invoice_data():
    all_owers = set()

    members = get_members(API_URL)

    debts = {}
    credits = {}

    api_response = requests.get("{}/bills".format(API_URL)).json()


    for row in api_response:
        owers = row['owers']
        amount_each = Decimal(row['amount']).quantize(TWOPLACES)
        amount_each /= len(owers)

        row['payer'] = members[row['payer_id']]
        row['payer_name'] = row['payer']['name']

        if row['what'] == 'deleteMeIfYouWant':
            continue

        if len(owers) > 1:
            what = "1/{0} {1}".format(len(owers), row['what'])
        else:
            what = row['what']

        doc = {
            'date'   : row['date'],
            'who'    : row['payer_name'],
            'amount' : amount_each.quantize(TWOPLACES),
            'what'   : what,
            'category' : CATEGORIES.get(row.get('category_id'), ''),
        }

        for ower in owers:
            all_owers.add(ower['name'])
            if ower['id'] not in debts:
                debts[ower['id']] = [doc,]
            else:
                debts[ower['id']].append(doc)

        doc = {
            'date'   : row['date'],
            'who'    : row['payer_name'],
            'amount' : -amount_each.quantize(TWOPLACES),
            'what'   : what,
            'category' : CATEGORIES.get(row.get('category_id'), ''),
        }

        if row['payer_id'] not in credits:
            credits[row['payer_id']] = [doc,]
        else:
            credits[row['payer_id']].append(doc)

    return {
        'debts' : debts,
        'credits' : credits,
    }


@app.route('/')
def index():
    members = get_members()
    return render_template("index.html", members=members)


@app.route('/invoice/<int:idx>')
def invoice(idx):
    ctx = parse_invoice_data()
    return render_template("invoice.html",
        debts=ctx['debts'].get(idx),
        credits=ctx['credits'].get(idx),
    )

#for ower in all_owers:
#    with open("{0}.csv".format(ower), 'w') as f:
#        fieldnames = ['date', 'what', 'who', 'amount', 'category']
#        writer = csv.DictWriter(f, fieldnames=fieldnames)
#        writer.writeheader()
#
#        for row in debts[ower]:
#            writer.writerow(row)
#
#        for row in credits[ower]:
#            writer.writerow(row)
#




