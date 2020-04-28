"""Script for sending a text message to a list of phone numbers extracted from a CSV file.

Run with environment variables set to find the aws.config and aws-credentials.config as in:

$> AWS_SHARED_CREDENTIALS_FILE=aws-credentials.config AWS_CONFIG_FILE=aws.config python sms_sender.py --roster school-roster.csv
"""

import argparse
import boto3
import csv
import logging
import sys
import time


# Phone numbers to skip because we sent them texts on previous runs. Format like:
ALREADY_SENT = [
#   '4156992016',
]


_AUCTION_MESSAGE_PREORDER = '''
Auction Night is Friday March 13th.
Buy your tickets by March 7th and save $15!
www.newtraditionssf.com/tickets
More info @
www.newtraditionssf.com/auction
'''


_AUCTION_MESSAGE_FINAL_PREORDER = '''
NT Auction Night early bird ticket prices end soon!
Buy your tickets before Saturday!
www.newtraditionssf.com/tickets
Auction Night is Friday March 13th @ 6pm
'''


_AUCTION_MESSAGE_FINAL = '''
Auction Night is Friday March 13th.
Buy your tickets now and avoid waiting in line!
www.newtraditionssf.com/tickets
More info @
www.newtraditionssf.com/auction
'''


_AUCTION_MESSAGE_CLOSE_LIVE = '''
LIVE auction items close tonight @ 9pm!
Don't get outbid!
www.newtraditionssf.com/live
'''


_AUCTION_MESSAGE_CLOSE_FINAL = '''
ALL auction items close tonight @ 9pm!
Get your final bids in now!
www.newtraditionssf.com/silent
'''


_AUCTION_MESSAGE = _AUCTION_MESSAGE_CLOSE_FINAL


_SECS_BETWEEN_SENDS = 0.5


def normalize_phone(phone_number_str):
    if not phone_number_str:
        return None
    digits_only = ''.join(c for c in phone_number_str if c.isdigit())

    if not digits_only:
        return None

    if digits_only in ALREADY_SENT:
        logging.debug('Skipping %s which was already successfully notified', digits_only)
        return None

    return '+1 {}'.format(digits_only)


def extract_parent_phone_numbers(roster_filename):
    """Return a numerically sorted list of unique phone numbers extracted from the file."""
    phone_number_set = set()
    num_rows = 0
    with open(roster_filename, 'r') as roster_file:
        roster_reader = csv.DictReader(roster_file)
        for row in roster_reader:
            for phone_cell in ['parent1_cell_phone', 'parent2_cell_phone']:
                # Some phone number entries are comma-separated lists.
                for phone in row[phone_cell].split(','):
                    normalized_phone = normalize_phone(phone)
                    if normalized_phone:
                        phone_number_set.add(normalized_phone)
            num_rows += 1

    logging.debug('Extracted %d phone numbers from %d lines', len(phone_number_set), num_rows)

    phone_number_list = [phone_number for phone_number in phone_number_set]
    phone_number_list.sort()
    return phone_number_list


def main():
    parser = argparse.ArgumentParser(description='Sends text messages to school parents.')
    parser.add_argument(
        '--dryrun', default=True, action='store_true',
        help='[DEFAULT] Do not actually send messages.')
    parser.add_argument(
        '--no-dryrun', dest='dryrun', action='store_false',
        help='Do actually send messages.')
    parser.add_argument(
        '--debug', default=False, action='store_true',
        help='Set to include debug messages.')
    parser.add_argument(
        '--sleep', default=_SECS_BETWEEN_SENDS, type=float,
        help='Override the amount of time between SMS sends to prevent throttling.')
    parser.add_argument(
        '--start', default=0, type=int,
        help='Starting offset (0-based) within the list of phone numbers.')
    parser.add_argument(
        '--count', default=10, type=int,
        help='Number of phone numbers to include.')
    parser.add_argument(
        'roster', type=unicode, help='Filename containing CSVs with a column named "phone"')
    args = parser.parse_args()

    is_dry_run = args.dryrun
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    phone_numbers = extract_parent_phone_numbers(args.roster)
    phone_number_subset = phone_numbers[args.start:args.start+args.count]
    logging.debug(
        'Sending to %d phone numbers out of full set of size %d. First number: %r',
        len(phone_number_subset),
        len(phone_numbers),
        phone_number_subset[0],
    )

    session = boto3.Session(profile_name='default')
    sns = session.client('sns')

    for phone_number in phone_number_subset:
        if is_dry_run:
            logging.debug('Skipping message in dryrun to: %s', phone_number)
        else:
            logging.debug('Sending message to: %s', phone_number)
            response = sns.publish(
                PhoneNumber=phone_number,
                Message=_AUCTION_MESSAGE,
            )
            logging.debug('Response after sending to %s: %r', phone_number, response)

        time.sleep(args.sleep)

    return 0

if __name__ == "__main__":
    sys.exit(main())
