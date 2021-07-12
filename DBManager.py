from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

class DBManager:
    """
    Class handling database connection.
    """
    def __init__(self):
        self.Base = declarative_base()
        self.engine = create_engine('sqlite:///example.db', future=True, echo=True, connect_args={'timeout': 5})
        #self.engine = create_engine('sqlite://', future=True, echo=True)
        self.Session = sessionmaker(bind=self.engine, future=True)

dbmanager = DBManager()
'''
with dbmanager.Session.begin() as session:
    # clearing music queue cache in database
    session.execute("DELETE FROM Queue")
'''