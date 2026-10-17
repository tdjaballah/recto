from datetime import datetime

from recto.ports.clock import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now().astimezone()
