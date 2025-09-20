from datetime import datetime


class HotelLog:
    def __init__(self):
        self.FILE = "log/log.txt"

    def addError(self, t):
        with open(self.FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] ERROR: {t}\n")


    def addInfo(self, t):
        with open(self.FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] INFO: {t}\n")