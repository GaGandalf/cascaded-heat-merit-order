import datetime
import unittest

from cascaded_heat_merit_order.utils import datetime_range


class TestUtils(unittest.TestCase):
    def test_datetime_range(self):
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        datetime_range_frequency = datetime.timedelta(hours=1)

        dt_range = datetime_range(start=yesterday, end=now, delta=datetime_range_frequency)
        self.assertEqual(min(dt_range), yesterday)
        self.assertEqual(max(dt_range), now - datetime_range_frequency)
        self.assertEqual(len(dt_range), 24)
