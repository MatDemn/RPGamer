from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float
from DBManager import dbmanager

class DiceResultModel(dbmanager.Base):
    """
    Class representing table 'DiceResult'.
    Contains information about rolls.
    """
    __tablename__ = "DiceResult"
    

    ID_DiceResults = Column(Integer, primary_key=True)
    ID_User = Column(Integer, ForeignKey('UserNameBackup.ID_User'))
    DiceLabel = Column(Integer)
    AvgResults = Column(Float)
    NumberOfResults = Column(Integer)

    def __init__(self, DiceLabel, AvgResults, NumberOfResults):
        self.DiceLabel = DiceLabel
        self.AvgResults = AvgResults
        self.NumberOfResults = NumberOfResults

    def __repr__(self):
        return f"<DiceResult(DiceLabel={self.DiceLabel}, AvgResults={self.AvgResults}," \
               f"NumberOfResults={self.NumberOfResults})>"

