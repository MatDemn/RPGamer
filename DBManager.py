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
        if 'DATABASE_URL' in os.environ:
            uri = os.environ['DATABASE_URL']
            # this is very stupid, but isn't work otherwise
            if uri.startswith("postgres://"):
                uri = uri.replace("postgres://", "postgresql://", 1)
            self.engine = create_engine(uri, future=True, echo=True)
        else:
            self.engine = create_engine('postgresql://zpvmpfsbnnipvw:6c42b97497f5c5ccd987badd132a9494b0779cc4534de48367445b4cda2d06a5@ec2-54-217-195-234.eu-west-1.compute.amazonaws.com:5432/datbrjup463jao', future=True, echo=True)
        #self.engine = create_engine('sqlite://', future=True, echo=True)
        self.Session = sessionmaker(bind=self.engine, future=True)

dbmanager = DBManager()
'''
with dbmanager.Session.begin() as session:
    # clearing music queue cache in database
    session.execute("DELETE FROM Queue")
'''