import random
from datetime import datetime, timedelta
from django.utils import timezone


def random_date():
    now = datetime.now(tz=timezone.utc)
    return now + timedelta(random.uniform(-1, 0) * 100)


def parse_date(raw):
    return datetime.strptime(raw, "%d.%m.%Y").date()


def random_timedelta(factor=100):
    return timedelta(random.uniform(0, 1) * factor)


def random_bool():
    return bool(random.getrandbits(1))