"""
Errors for bot use.
"""

class NoVoiceChannel(Exception):
    def __init__(self):
        super().__init__('You have to be in a voice channel...')

class QueueFull(Exception):
    def __init__(self):
        super().__init__("You've reached music queue limit...")

class WrongArgument(Exception):
    def __init__(self, msg=None):
        if msg:
            super().__init__(msg)
        else:
            super().__init__("You passed wrong argument...")

class GMOrAdmin(Exception):
    def __init__(self):
        super().__init__("You have to be GM of this session or Admin to change it.")