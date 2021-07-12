import enum


class LanguageEnum(enum.Enum):
    """
    Language enum. May be used in future.
    """
    pl = 1
    en = 2


class SoundReactionEnum(enum.Enum):
    """
    Enum for bot soundboard reactions for rolls.
    """
    none = 1
    good = 2
    bad = 3

