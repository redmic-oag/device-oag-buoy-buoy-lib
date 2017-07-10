import unittest

from buoy.lib.notification.server import Notification


class TestConsoleCLI(unittest.TestCase):

    def test_run_weather_station(self):
        Notification()


if __name__ == '__main__':
    unittest.main()
