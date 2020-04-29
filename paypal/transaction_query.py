#! /bin/bash python

import argparse
from config import paypal_init
from datetime import (
    datetime,
    timedelta,
)
import logging
import requests
import sys


def _iso_utc_str(datetime_obj):
    return '%sZ' % datetime_obj.isoformat(timespec='seconds')


def _filter_transactions(transaction_response):
    """Extract a list of paypal `transaction_detail` objects that are for yearbook items.
    """
    transaction_details = transaction_response['transaction_details']
    return [
        transaction_detail for transaction_detail in transaction_details
        if _is_yearbook_transaction(transaction_detail)
    ]

def _is_yearbook_transaction(transaction_detail):
    """Returns True iff the paypal `transaction_detail` object contains an `item_name` of Yearbook.
    """
    cart_info = transaction_detail.get('cart_info')
    if cart_info:
        item_details = cart_info.get('item_details')
        if item_details and len(item_details) == 1:
            item = item_details[0]
            item_name = item.get('item_name', '').lower()
            return item_name and item_name.find('yearbook') != -1

    transaction_info = transaction_detail.get('transaction_info')
    if transaction_info:
        invoice_id = transaction_info.get('invoice_id', '').lower()
        return invoice_id and invoice_id.find('yearbook-invoice') != -1

    return False


def _print_transactions(transaction_details):
    """Print as CSV the details of each transaction."""
    for transaction_detail in transaction_details:
        logging.debug('transaction_detail: %r', transaction_detail)
        transaction_info = transaction_detail['transaction_info']
        amount_paid = transaction_info['transaction_amount']['value']
        invoice_id = transaction_info['invoice_id']
        tx_date = transaction_info['transaction_initiation_date']

        payer_info = transaction_detail['payer_info']
        payer_email = payer_info.get('email_address', 'missing-email')
        payer_name = payer_info['payer_name']['alternate_full_name']
        print('%s,%s,%s,%s,%s' % (tx_date, payer_email, payer_name, invoice_id, amount_paid))


def main():
    parser = argparse.ArgumentParser(description='Fetches and formats recent paypal transactions.')
    parser.add_argument(
        '--debug', default=False, action='store_true',
        help='Set to include debug messages.')
    parser.add_argument(
        '--start-date',
        help='Optional ISO format for starting date of query (e.g. 2020-04-29T05:07:57Z).')
    parser.add_argument(
        '--end-date',
        help='Optional ISO format for ending date of query (e.g. 2020-04-29T05:07:57Z).')
    parser.add_argument(
        '--fetch-count', default=100,
        help='Number of transactions to fetch.')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    iso_end_date = args.end_date
    if not iso_end_date:
        end_date = datetime.utcnow()
        iso_end_date = _iso_utc_str(end_date)

    iso_start_date = args.start_date
    if not iso_start_date:
        if not end_date:
            end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        iso_start_date = _iso_utc_str(start_date)

    config = paypal_init()
    logging.debug('Config: %r', config,)

    request_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % config['access_token'],
    }
    request_params = dict(
        start_date=iso_start_date,
        end_date=iso_end_date,
        fields='all',
        page_size=args.fetch_count,
        page=1,
    )
    logging.debug(
        'Request with headers=%r, params=%r',
        request_headers,
        request_params,
    )
    transaction_response = requests.get(
        'https://api.paypal.com/v1/reporting/transactions',
        headers=request_headers,
        params=request_params,
    )

    if transaction_response.ok:
        transaction_json = transaction_response.json()

        logging.debug('Response json: %r', transaction_json)

        filtered_transactions = _filter_transactions(transaction_json)
        logging.debug('Yearbook transactions: %r', filtered_transactions)

        _print_transactions(filtered_transactions)
        return 0

    else:
        logging.error(
            'Request failed with status=%r: %r',
            transaction_response.status_code,
            transaction_response.text,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())

