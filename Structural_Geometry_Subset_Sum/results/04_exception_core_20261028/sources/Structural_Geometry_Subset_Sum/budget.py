"""Shared online resource accounting; exhaustion is never a NO certificate."""
from time import perf_counter


class ResourceLimit(Exception):
    pass


class CheckLimit(Exception):
    pass


class Meter:
    def __init__(self, max_work, seconds=None):
        if type(max_work) is not int or max_work < 1:
            raise ValueError("positive integer work cap required")
        if seconds is not None and not 0 < seconds < float("inf"):
            raise ValueError("finite positive seconds required")
        self.started = perf_counter()
        self.deadline = None if seconds is None else self.started + seconds
        self.max_work, self.work = max_work, 0
        self.peak_dp_bits = self.peak_history_bits = self.peak_search_states = 0

    @property
    def remaining(self):
        return self.max_work-self.work

    def tick(self, amount=1):
        if amount < 0 or self.work+amount > self.max_work:
            raise ResourceLimit("work_limit")
        self.work += amount
        self.check()

    def check(self):
        if self.deadline is not None and perf_counter() >= self.deadline:
            raise ResourceLimit("deadline")

    def seconds_left(self):
        self.check()
        return None if self.deadline is None else max(1e-9, self.deadline-perf_counter())


class LocalMeter:
    """A bounded check can stop while leaving the shared fallback budget intact."""
    def __init__(self, parent, max_work):
        self.parent, self.max_work, self.work = parent, max_work, 0

    def tick(self, amount=1):
        if self.work+amount > self.max_work:
            raise CheckLimit("check_work_limit")
        self.parent.tick(amount)
        self.work += amount

    def check(self):
        self.parent.check()
