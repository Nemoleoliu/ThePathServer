import argparse
from sqlalchemy import create_engine
from config import CONFIG
from data_models import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Setup db.')
    parser.add_argument('--dropfirst', dest='dropfirst',action='store_const', const=True, default=False,
                        help = 'WARNING!!!This will drop all table first and recreate them.')
    parser.add_argument('--fakedata', dest='fakedata',action='store_const', const=True, default=False,
                        help = 'Fake some data.')
    parser.add_argument('-d', dest='debug', action='store_const', const=True, default=False,
                        help='Debug mode enabled.')
    args = parser.parse_args()
    engine = create_engine(CONFIG['database_engine'], echo=args.debug)
    if args.dropfirst:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
