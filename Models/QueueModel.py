from sqlalchemy import Column, Integer, String, Boolean, Enum
from DBManager import dbmanager


class QueueModel(dbmanager.Base):
    """
    Class representing table 'Queue'.
    Contains information about music queue.
    """
    __tablename__ = "Queue"
    

    ID_Queue = Column(Integer, primary_key=True)
    ID_Server = Column(Integer)
    Entry = Column(String)
    FullName = Column(String)

    def __init__(self, ID_Server, Entry, FullName):
        self.ID_Server = ID_Server
        self.Entry = Entry
        self.FullName = FullName

    def __repr__(self):
        return f"<Queue(ID_Queue={self.ID_Queue}, " \
               f"ID_Server={self.ID_Server}, Entry={self.Entry}, FullName={self.FullName})>"
