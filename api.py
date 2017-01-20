from flask_restful import Api, Resource, fields, marshal_with
from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import CONFIG
from data_models import Account, Transaction, Bank, User, Tag

app = Flask(__name__)
api = Api(app, prefix='/api')
engine = create_engine(CONFIG['database_engine'])
Session = sessionmaker(bind=engine)
session = Session()


class IndexAPI(Resource):
    def get(self):
        return {
            'data': 'success'
        }

class AccountsAPI(Resource):
    @marshal_with(Account.BASE_FIELDS)
    def get(self):
        accounts = session.query(Account).all()
        return accounts


class AccountAPI(Resource):
    @marshal_with(Account.BASE_FIELDS)
    def get(self, id):
        account = session.query(Account).get(id)
        return account


class TransactionsAPI(Resource):
    @marshal_with(Transaction.BASE_FIELDS)
    def get(self):
        transactions = session.query(Transaction).all()
        return transactions


class TransactionAPI(Resource):
    @marshal_with(Transaction.BASE_FIELDS)
    def get(self, id):
        transaction = session.query(Transaction).get(id)
        return transaction


class TransactionTagsAPI(Resource):
    @marshal_with(Tag.BASE_FIELDS)
    def get(self, id):
        tags = session.query(Transaction).get(id).tags
        return tags

    @marshal_with(Tag.BASE_FIELDS)
    def post(self, id):
        json_data = request.get_json(force=True)
        transaction = session.query(Transaction).get(id)
        for d in json_data:
            if 'name' in d:
                tag = session.query(Tag).filter(Tag.name==d['name']).first()
                if not tag:
                    tag = Tag(name=d['name'])
                    session.add(tag)
            elif 'id' in d:
                tag = session.query(Tag).get(d['id'])
                if not tag:
                    #todo exception handle
                    pass
            else:
                #todo exception handle
                pass
            transaction.tags.append(tag)
        session.commit()
        return transaction.tags


class BanksAPI(Resource):
    @marshal_with(Bank.BASE_FIELDS)
    def get(self):
        banks = session.query(Bank).all()
        return banks


class BankAPI(Resource):
    @marshal_with(Bank.BASE_FIELDS)
    def get(self, id):
        bank = session.query(Bank).get(id)
        return bank


class TagAPI(Resource):
    @marshal_with(Bank.BASE_FIELDS)
    def get(self, id):
        bank = session.query(Bank).get(id)
        return bank

api.add_resource(IndexAPI, '/')
api.add_resource(AccountsAPI, '/accounts')
api.add_resource(AccountAPI, '/accounts/<int:id>')
api.add_resource(TransactionsAPI, '/transactions')
api.add_resource(TransactionAPI, '/transactions/<int:id>')
api.add_resource(TransactionTagsAPI, '/transactions/<int:id>/tags')
api.add_resource(BanksAPI, '/banks')
api.add_resource(BankAPI, '/banks/<int:id>')


if __name__ == '__main__':
    app.run(debug=True)