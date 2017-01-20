import argparse
from datetime import datetime

from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import CONFIG
from data_models import *
from ofxutils import Client


def get_all_account(session):
    accounts = session.query(Account).filter(Account.auto==True).filter(Account.available==True).all()
    return accounts


def query_ofx(account):
    if account.type == AccountTypeEnum.credit:
        client = Client(account)
        resp = client.post(client.credit_card_account_query())
    else:
        client = Client(account)
        resp = client.post(client.bank_account_query())
    return resp


def push_unconfirmed_transaction():
    pass


def write_db():
    pass


def push_notification():
    pass


def runMainLoop(debug):
    engine = create_engine(CONFIG['database_engine'], echo=debug)
    Session = sessionmaker(bind=engine)
    session = Session()
    # push_unconfirmed_transaction()
    # while True:
    accounts = get_all_account(session)
    for account in accounts:
        resp = query_ofx(account)
        soup = BeautifulSoup(resp, 'html.parser')
        last_date = soup.find('banktranlist').find('dtend').contents[0].strip()
        balance = soup.find('balamt').contents[0].strip()
        count = 0
        for s in soup.find_all('stmttrn'):
            trn_type = s.find('trntype').contents[0].strip()
            date = s.find('dtposted').contents[0].strip()
            amount = s.find('trnamt').contents[0].strip()
            name = s.find('name').contents[0].strip()
            fitid = s.find('fitid').contents[0].strip()
            memo = None
            if s.find('memo'):
                memo =  s.find('memo').contents[0].strip()
                name = "".join([name, memo])
            trans_date = datetime.strptime(date[:14], '%Y%m%d%H%M%S')
            transaction = Transaction(amount=amount,
                                      account_id=account.id,
                                      description=name,
                                      date=trans_date,
                                      ori_type=trn_type,
                                      ori_name=name,
                                      ori_memo=memo,
                                      ori_fitid=fitid,
                                      ori_amount=amount,
                                      ori_postdate=date
                                      )
            google = session.query(Tag).get(1)
            facebook = session.query(Tag).get(2)
            transaction.tags.append(google)
            transaction.tags.append(facebook)
            session.add(transaction)
            count += 1
        print '{1} transactions added to account {0}'.format(account.name, count)
        account.last_date = last_date
        account.balance = balance
        session.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Setup db.')
    parser.add_argument('-d', dest='debug', action='store_const', const=True, default=False,
                        help='Debug mode enabled.')
    args = parser.parse_args()
    runMainLoop(args.debug)
