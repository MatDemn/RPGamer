from sqlalchemy import Column, Integer, String, Boolean, Enum, BigInteger
from sqlalchemy.orm import relationship
from DBManager import dbmanager
from .LanguageEnum import LanguageEnum

from .DiceResultModel import DiceResultModel
from .UserNameModel import UserNameModel


class ServerSessionModel(dbmanager.Base):
    """
    Class representing table 'ServerSession'.
    Contains information about session structure.
    """
    __tablename__ = "ServerSession"
    

    ID_ServerSession = Column(Integer, primary_key=True, autoincrement=True)
    ID_Server = Column(BigInteger)
    SessionShort = Column(String)
    ID_GM = Column(BigInteger)
    SoundBoardSwitch = Column(Boolean)

    UsersNames = relationship("UserNameModel", cascade="all, delete, delete-orphan")

    def __init__(self, ID_Server, SessionShort, ID_GM, soundBoard):
        self.ID_Server = ID_Server
        self.SessionShort = SessionShort
        self.ID_GM = ID_GM
        self.SoundBoardSwitch = soundBoard

    def __repr__(self):
        return f"<Session(ID_ServerSession={self.ID_ServerSession}, " \
               f"ID_Server={self.ID_Server}, SessionShort={self.SessionShort}" \
               f"ID_GM={self.ID_GM}, SoundBoard={self.SoundBoardSwitch})>"
