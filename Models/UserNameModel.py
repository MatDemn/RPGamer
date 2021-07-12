from sqlalchemy import Column, Integer, String, ForeignKey
from DBManager import dbmanager


class UserNameModel(dbmanager.Base):
    """
    Class representing table 'UserName'.
    Contains information about hero names for players.
    """
    __tablename__ = "UserName"
    

    ID_UserName = Column(Integer, primary_key=True)
    ID_ServerSession = Column(Integer, ForeignKey('ServerSession.ID_ServerSession'))
    HeroName = Column(String)
    ID_User = Column(Integer, ForeignKey('UserNameBackup.ID_User'))

    def __init__(self, HeroName):
        self.HeroName = HeroName

    def __repr__(self):
        return f"<UserName(ID_UserName={self.ID_UserName}, " \
               f"ServerSession={self.ID_ServerSession}, HeroName={self.HeroName}, " \
               f"ID_User={self.ID_User})>"


