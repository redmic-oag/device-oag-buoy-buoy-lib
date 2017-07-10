import unittest

from nose.tools import ok_

from buoy.lib.protocol.item import DataEncoder
from buoy.lib.protocol.nmea0183 import WIMDA
from buoy.lib.notification.common import NoticeData
from datetime import datetime, timezone
import json


class TestNotificationSerialize(unittest.TestCase):
    def setUp(self):
        now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z")

        self.data = {
            'id': None,
            'datetime': now,
            'air_temperature': '26.8',
            'barometric_pressure_inch': '30.3273',
            'barometric_pressure_bar': '1.027',
            'water_temperature': '20.1',
            'relative_humidity': '12.3',
            'absolute_humidity': '21.0',
            'dew_point': '2.3',
            'wind_direction_true': '2.0',
            'wind_direction_magnetic': '128.7',
            'wind_speed_knots': '134.6',
            'wind_speed_meters': '0.3'
        }

        self.notification_expected = NoticeData(datetime=now, data=WIMDA(**self.data))

    def test_wimda_serialize(self):
        serial = json.dumps(self.notification_expected, cls=DataEncoder, sort_keys=True)
        json_expected = ('"data": {{"absolute_humidity": {absolute_humidity}, '
                         '"air_temperature": {air_temperature}, '
                         '"barometric_pressure_bar": {barometric_pressure_bar}, '
                         '"barometric_pressure_inch": {barometric_pressure_inch}, '
                         '"datetime": "{datetime}", '
                         '"dew_point": {dew_point}, '
                         '"relative_humidity": {relative_humidity}, '
                         '"water_temperature": {water_temperature}, '
                         '"wind_direction_magnetic": {wind_direction_magnetic}, '
                         '"wind_direction_true": {wind_direction_true}, '
                         '"wind_speed_knots": {wind_speed_knots}, '
                         '"wind_speed_meters": {wind_speed_meters}}}').format(**dict(self.data))

        ok_(json_expected in str(serial))

if __name__ == '__main__':
    unittest.main()

