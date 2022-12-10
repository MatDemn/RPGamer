from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

class DBManager:
    """
    Class handling database connection.
    """
    def __init__(self):
        self.Base = declarative_base()
        #if 'DATABASE_URL' in os.environ:
        #    uri = os.environ['DATABASE_URL']
        #    # this is very stupid, but isn't work otherwise
        #    if uri.startswith("postgres://"):
        #        uri = uri.replace("postgres://", "postgresql://", 1)
        #    self.engine = create_engine(uri, future=True, echo=True)
        #else:
        #    self.engine = create_engine('postgresql://viuaugsugdvrpv:073c54d58241d4959b7764fea64fb39a28a1a99e1b109bb5c043d3eca14f5e00@ec2-34-246-24-110.eu-west-1.compute.amazonaws.com:5432/d7joef1t7h2s8v', future=True, echo=True)
        self.engine = create_engine('sqlite://', future=True, echo=True)
        self.Session = sessionmaker(bind=self.engine, future=True)

dbmanager = DBManager()
'''
with dbmanager.Session.begin() as session:
    # clearing music queue cache in database
    session.execute("DELETE FROM Queue")
'''