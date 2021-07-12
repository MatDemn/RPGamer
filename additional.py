import sys
import datetime

def cprint(string):
    """
    Sometimes used to debug code. Prints information about error and some debug info.
    :param string: String with error content.
    """
    callername = sys._getframe().f_back.f_code.co_name
    print(f"{datetime.datetime.now()} [{callername}]: \"{string}\"")
        
def dumplog(string):
    """
    Sometimes used to debug code. Prints error info to file as logs.
    :param string: String with error content.
    """
    cprint("Error dumped into dumplog.txt")
    with open("errorLog.txt", mode="a", encoding="utf-8") as file:
        file.write(f"{string}")
    