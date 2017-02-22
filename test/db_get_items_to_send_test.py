import unittest
import psycopg2
import testing.postgresql

from buoy.lib.device.currentmeter.acmplus import ACMPlusItem
from buoy.lib.protocol.nmea0183 import WIMDA
from buoy.lib.device.base import DeviceDB

from nose.tools import eq_, ok_

db = None
db_con = None
db_conf = None


class BaseDBGetItemsTests(unittest.TestCase):
    item_class = None
    db_tablename = None

    @classmethod
    def setUpClass(cls):
        if cls is BaseDBGetItemsTests:
            raise unittest.SkipTest("Skip BaseTest tests, it's a base class")
        super(BaseDBGetItemsTests, cls).setUpClass()

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

        with open('test/data_example.sql', 'r') as fh:
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

    def test_get_items_in_db(self):

        dev_db = DeviceDB(
            connection_db=db_con,
            tablename_data=self.db_tablename
        )

        rows = dev_db.get_items_to_send()
        items = []
        for row in rows:
            items.append(self.item_class(**row))

        eq_(len(rows), 15)
        ok_(all(a.id <= b.id for a, b in zip(items[:-1], items[1:])))


class TestACMPlus(BaseDBGetItemsTests):
    item_class = ACMPlusItem
    db_tablename = "acmplus"


class TestPB200(BaseDBGetItemsTests):
    item_class = WIMDA
    db_tablename = "pb200"

if __name__ == '__main__':
    unittest.main()
