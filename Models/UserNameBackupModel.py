from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from DBManager import dbmanager


class UserNameBackupModel(dbmanager.Base):
    """
    Class representing table 'UserNameBackup'.
    Contains information about users names backup.
    """
    __tablename__ = "UserNameBackup"
    

    ID_User = Column(Integer, primary_key=True)
    NickBackup = Column(String)
    SoundBoardSwitch = Column(Boolean)

    UsersNames = relationship("UserNameModel", cascade="all, delete, delete-orphan")
    DicesResults = relationship("DiceResultModel", cascade="all, delete, delete-orphan")

    def __init__(self, ID_User, NickBackup, soundBoard):
        self.ID_User = ID_User
        self.NickBackup = NickBackup
        self.SoundBoardSwitch = soundBoard

    def __repr__(self):
        return f"<UserNameBackup(ID_User={self.ID_User}, " \
               f"NickBackup={self.NickBackup}," \
               f"SoundBoard={self.SoundBoardSwitch})>"


