import unittest
import psycopg2
import testing.postgresql

from datetime import datetime
from buoy.lib.device.currentmeter.acmplus import ACMPlusItem
from buoy.lib.protocol.nmea0183 import WIMDA
from buoy.lib.device.base import DeviceDB

from nose.tools import eq_

db = None
db_con = None
db_conf = None


class BaseDBTests(unittest.TestCase):
    item_class = None
    data = None

    @classmethod
    def setUpClass(cls):
        if cls is BaseDBTests:
            raise unittest.SkipTest("Skip BaseTest tests, it's a base class")
        super(BaseDBTests, cls).setUpClass()

    def setUp(self):
        """ Module level set-up called once before any tests in this file are executed. Creates a temporary database
        and sets it up """

        global db, db_con, db_conf
        db = testing.postgresql.Postgresql()
        # Get a map of connection parameters for the database which can be passed
        # to the functions being tested so that they connect to the correct
        # database
        db_conf = db.dsn()
        # Create a connection which can be used by our test functions to set and
        # query the state of the database
        db_con = psycopg2.connect(**db_conf)
        # Commit changes immediately to the database
        db_con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        with open('setup.sql', 'r') as fh:
            lines_str = fh.read()

        with db_con.cursor() as cur:
            # Create the initial database structure (roles, schemas, tables etc.)
            # basically anything that doesn't change
            cur.execute(lines_str)

    def tearDown(self):
        """ Called after all of the tests in this file have been executed to close the database connecton and destroy
        the temporary database """

        db_con.close()
        db.stop()

    def test_add_item_in_db(self):

        item_to_insert = self.item_class(**self.data)

        dev_db = DeviceDB(
            db_config=db_conf,
            db_tablename=self.db_tablename
        )

        dev_db.save([item_to_insert])

        with db_con.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""SELECT * FROM %s""" % (self.db_tablename,))
            rows = cur.fetchall()

            eq_(len(rows), 1)
            row = rows[0]
            for key, value in self.data.items():
                eq_(row[key], value)

            eq_(row['id'], 1)


class TestACMPlus(BaseDBTests):
    item_class = ACMPlusItem
    db_tablename = "acmplus"
    data = {
            'datetime': datetime.now(),
            'vx': 30.3273,
            'vy': 1.0270,
            'speed': 20.1,
            'direction': 26.8,
            'water_temperature': 12.3
        }


class TestPB200(unittest.TestCase):
    item_class = WIMDA
    db_tablename = "pb200"
    data = {
        'datetime': datetime.now(),
        'barometric_pressure_inch': 30.3273,
        'barometric_pressure_bar': 1.0270,
        'air_temperature': 26.8,
        'water_temperature': 20.1,
        'relative_humidity': 12.3,
        'absolute_humidity': 21.0,
        'dew_point': 2.3,
        'wind_direction_true': 2.0,
        'wind_direction_magnetic': 128.7,
        'wind_speed_knots': 134.6,
        'wind_speed_meters': 0.3
    }


if __name__ == '__main__':
    unittest.main()
