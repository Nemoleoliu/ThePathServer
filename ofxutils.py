import time
from datetime import datetime
import uuid
from httplib import HTTPSConnection
from urllib import splittype, splithost

from data_models import AccountTypeEnum

DEFAULT_APP_ID = 'QWIN'
DEFAULT_APP_VERSION = '2200'
DEFAULT_OFX_VERSION = '103'

LINE_ENDING = "\r\n"


def ofx_uid():
    return str(uuid.uuid4().hex)

class Client:

    def __init__(
        self,
        account,
        app_id=DEFAULT_APP_ID,
        app_version=DEFAULT_APP_VERSION,
        ofx_version=DEFAULT_OFX_VERSION
    ):
        self.account = account
        self.app_id = app_id
        self.app_version = app_version
        self.ofx_version = ofx_version
        self.cookie = 3

    def authenticated_query(
        self,
        with_message=None,
        username=None,
        password=None
    ):
        """Authenticated query

        If you pass a 'with_messages' array those queries will be passed along
        otherwise this will just be an authentication probe query only.
        """
        u = username or self.account.username
        p = password or self.account.password

        contents = ['OFX', self._signOn(username=u, password=p)]
        if with_message:
            contents.append(with_message)
        return LINE_ENDING.join([self.header(), _tag(*contents)])

    def bank_account_query(self):
        """Bank account statement request"""
        return self.authenticated_query(self._bareq())

    def credit_card_account_query(self):
        """CC Statement request"""
        return self.authenticated_query(self._ccreq())

    def brokerage_account_query(self, number, date, broker_id):
        return self.authenticated_query(
            self._invstreq(broker_id, number, date))

    def account_list_query(self, date='19700101000000'):
        return self.authenticated_query(self._acctreq(date))

    def post(self, query):
        # print('posting data to %s' % i.url)
        # print('---- request ----')
        # print(query)
        garbage, path = splittype(self.account.bank.ofx_url)
        host, selector = splithost(path)
        h = HTTPSConnection(host, timeout=60)
        h.request('POST', selector, query,
                  {
                      "Content-type": "application/x-ofx",
                      "Accept": "*/*, application/x-ofx"
                  })
        res = h.getresponse()
        response = res.read().decode('ascii', 'ignore')
        # print('---- response ----')
        # print(res.__dict__)
        # print(response)
        res.close()

        return response

    def next_cookie(self):
        self.cookie += 1
        return str(self.cookie)

    def header(self):
        parts = [
            "OFXHEADER:100",
            "DATA:OFXSGML",
            "VERSION:%d" % int(self.account.bank.ofx_version or self.ofx_version),
            "SECURITY:NONE",
            "ENCODING:USASCII",
            "CHARSET:1252",
            "COMPRESSION:NONE",
            "OLDFILEUID:NONE",
            "NEWFILEUID:NONE",
            ""
        ]
        return LINE_ENDING.join(parts)

    """Generate signon message"""
    def _signOn(self, username=None, password=None):
        i = self.account
        u = username or i.username
        p = password or i.password
        fidata = [_field("ORG", self.account.bank.ofx_org)]
        if self.account.bank.ofx_id:
            fidata.append(_field("FID", self.account.bank.ofx_id))

        client_uid = ''
        if str(self.ofx_version) == '103':
            client_uid = _field('CLIENTUID', self.account.bank.ofx_clientid)

        return _tag("SIGNONMSGSRQV1",
                    _tag("SONRQ",
                         _field("DTCLIENT", now()),
                         _field("USERID", u),
                         _field("USERPASS", p),
                         _field("LANGUAGE", "ENG"),
                         _tag("FI", *fidata),
                         _field("APPID", self.app_id),
                         _field("APPVER", self.app_version),
                         client_uid
                         ))

    def _acctreq(self):
        dtstart = datetime.dat
        req = _tag("ACCTINFORQ", _field("DTACCTUP", dtstart))
        return self._message("SIGNUP", "ACCTINFO", req)

# this is from _ccreq below and reading page 176 of the latest OFX doc.
    def _bareq(self):
        dtstart = self.account.last_date or datetime(year=1970,month=1,day=1).strftime('%Y%m%d%H%M%S')
        req = _tag("STMTRQ",
                   _tag("BANKACCTFROM",
                        _field("BANKID", self.account.bank.routing_number),
                        _field("ACCTID", self.account.number),
                        _field("ACCTTYPE", 'CHECKING' if self.account.type is AccountTypeEnum.checking else 'SAVINGS')),
                   _tag("INCTRAN",
                        _field("DTSTART", dtstart),
                        _field("INCLUDE", "Y")))
        return self._message("BANK", "STMT", req)

    def _ccreq(self):
        dtstart = self.account.last_date or datetime(year=1970,month=1,day=1).strftime('%Y%m%d%H%M%S')
        req = _tag("CCSTMTRQ",
                   _tag("CCACCTFROM", _field("ACCTID", self.account.number)),
                   _tag("INCTRAN",
                        _field("DTSTART", dtstart),
                        _field("INCLUDE", "Y")))
        return self._message("CREDITCARD", "CCSTMT", req)

    # def _invstreq(self, brokerid, acctid, dtstart):
    #     req = _tag("INVSTMTRQ",
    #                _tag("INVACCTFROM",
    #                     _field("BROKERID", brokerid),
    #                     _field("ACCTID", acctid)),
    #                _tag("INCTRAN",
    #                     _field("DTSTART", dtstart),
    #                     _field("INCLUDE", "Y")),
    #                _field("INCOO", "Y"),
    #                _tag("INCPOS",
    #                     _field("DTASOF", now()),
    #                     _field("INCLUDE", "Y")),
    #                _field("INCBAL", "Y"))
    #     return self._message("INVSTMT", "INVSTMT", req)

    def _message(self, msgType, trnType, request):
        return _tag(msgType+"MSGSRQV1",
                    _tag(trnType+"TRNRQ",
                         _field("TRNUID", ofx_uid()),
                         _field("CLTCOOKIE", self.next_cookie()),
                         request))


def _field(tag, value):
    return "<"+tag+">"+value


def _tag(tag, *contents):
    return LINE_ENDING.join(['<'+tag+'>']+list(contents)+['</'+tag+'>'])


def now():
    return time.strftime("%Y%m%d%H%M%S", time.localtime())
