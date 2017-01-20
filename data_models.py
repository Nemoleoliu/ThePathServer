from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, Enum, DateTime, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask_restful import fields, marshal_with
import enum
import json


class AccountTypeEnum(enum.Enum):
    savings = "savings"
    checking = "checking"
    credit = "credit"


class TransactionTypeEnum(enum.Enum):
    traffic = "traffic"
    life = "life"
    learning = "learning"
    entertainment = "entertainment"
    other = "other"
    unset = "unset"


class EnumString(fields.Raw):
    def format(self, value):
        return value.value


class LastFourNumber(fields.Raw):
    def format(self, value):
        s = str(value)
        return s[-4:]


class BaseModel(object):
    def __repr__(self):
        d = {}
        for c in self.__table__.columns:
            v = getattr(self, c.name, None)
            if isinstance(v, basestring):
               pass
            elif isinstance(v, enum.Enum):
                v = v.value
            else:
                v = str(v)
            d[c.name] = v
        return json.dumps(d,indent=4, sort_keys=True)

Base = declarative_base(cls=BaseModel)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    username = Column(String(80), nullable=False, unique=True)
    password = Column(String(80), nullable=False)

    BASE_FIELDS = {
        'id': fields.String,
        'name': fields.String,
    }


class Bank(Base):
    __tablename__ = 'bank'

    id = Column(Integer, primary_key=True)
    ofx_id = Column(String(80), nullable=False)
    ofx_org = Column(String(255), nullable=False)
    ofx_url = Column(String(255), nullable=False)
    ofx_version = Column(String(80), nullable=False, default='103')
    ofx_clientid = Column(String(80))
    description = Column(String(80))
    routing_number = Column(String(80))
    accounts = relationship("Account", back_populates='bank')

    BASE_FIELDS = {
        'id': fields.String,
        'description': fields.String,
    }


class Account(Base):
    __tablename__ = 'account'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    number = Column(String(80), nullable=False)
    bank_id = Column(Integer, ForeignKey('{0}.id'.format(Bank.__tablename__)), nullable=False)
    bank = relationship("Bank", back_populates='accounts')
    type = Column(Enum(AccountTypeEnum), nullable=False)
    balance = Column(Numeric(12,2), nullable=False, default=0.0)
    owner = Column(Integer, ForeignKey('{0}.id'.format(User.__tablename__)), nullable=False)
    username = Column(String(80))
    password = Column(String(80))
    auto = Column(Boolean, nullable=False, default=True)
    available = Column(Boolean, nullable=False, default=True)
    last_date = Column(String(80))

    BASE_FIELDS = {
        'id': fields.String,
        'name': fields.String,
        'type': EnumString,
        'balance': fields.String,
        'number': LastFourNumber,
        'bank_id': fields.String,
        'auto': fields.Boolean,
    }

association_table = Table('tag_transaction', Base.metadata,
    Column("tag_id", Integer, ForeignKey("tag.id"), nullable=False),
    Column("tran_id", Integer, ForeignKey("transaction.id"), nullable=False)
)

class Transaction(Base):
    __tablename__ = 'transaction'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('{0}.id'.format(Account.__tablename__)), nullable=False)
    type = Column(Enum(TransactionTypeEnum), default=TransactionTypeEnum.other, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    date = Column(DateTime, nullable=False)
    is_notified = Column(Boolean, default=False, nullable=False)
    description = Column(String(80))
    ori_fitid = Column(String(80))
    ori_type = Column(String(80))
    ori_amount = Column(String(80))
    ori_name = Column(String(80))
    ori_memo = Column(String(80))
    ori_postdate = Column(String(80))
    tags = relationship('Tag', secondary=association_table, back_populates="transactions")

    BASE_FIELDS = {
        'id': fields.String,
        'account_id': fields.String,
        'type': EnumString,
        'amount': fields.String,
        'date': fields.DateTime,
        'description': fields.String,
        'is_notified': fields.Boolean,
    }


class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False, unique=True)
    transactions = relationship('Transaction', secondary=association_table, back_populates="tags")

    BASE_FIELDS = {
        'id': fields.String,
        'name': fields.String,
    }
