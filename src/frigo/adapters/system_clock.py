from datetime import date

from frigo.ports.clock import Clock


class SystemClock(Clock):
    def today(self) -> date:
        return date.today()
