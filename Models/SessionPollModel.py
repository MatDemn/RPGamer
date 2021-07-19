from sqlalchemy import Column, Integer, String, Boolean, Enum, Date, BigInteger
from sqlalchemy.orm import relationship
from DBManager import dbmanager
from .LanguageEnum import LanguageEnum


class SessionPollModel(dbmanager.Base):
    """
        Represents servers and date of their last session poll.
        Also, It shows if automatic poll making is enabled on server.
    """
    __tablename__ = "SessionPoll"

    ID_Server = Column(BigInteger, primary_key=True)
    LastPoll = Column(Date)
    IsEnabled = Column(Boolean)

    def __init__(self, ID_Server, LastPoll):
        self.ID_Server = ID_Server
        self.LastPoll = LastPoll
        self.IsEnabled = IsEnabled

    def __repr__(self):
        return f"<Session(ID_Server={self.ID_Server}, " \
               f"LastPoll={self.LastPoll}," \
               f"IsEnabled={self.IsEnabled})>"
