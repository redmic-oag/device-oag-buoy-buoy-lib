import unittest

from buoy.lib.notification.server import NotificationServer


class TestConsoleCLI(unittest.TestCase):

    def test_run_weather_station(self):
        NotificationServer()


if __name__ == '__main__':
    unittest.main()
