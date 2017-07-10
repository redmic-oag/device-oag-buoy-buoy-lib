import unittest
import psycopg2
import testing.postgresql

from buoy.lib.device.currentmeter.acmplus import ACMPlusItem
from buoy.lib.protocol.nmea0183 import WIMDA
from buoy.lib.device.base import DeviceDB
from buoy.lib.notification.common import Notification

from nose.tools import eq_, ok_

db = None
db_con = None
db_conf = None
skip_test = False


class BaseDBGetItemsTests(unittest.TestCase):
    item_class = None
    db_tablename = None

    @classmethod
    def setUpClass(cls):
        global skip_test
        if cls is BaseDBGetItemsTests:
            skip_test = True
        else:
            skip_test = False
        super(BaseDBGetItemsTests, cls).setUpClass()

    def tearDown(self):
        """ Called after all of the tests in this file have been executed to close the database connecton and destroy
        the temporary database """
        if skip_test:
            self.skipTest("Skip BaseTest tests, it's a base class")

        db_con.close()
        db.stop()

    def prepareDB(self, path_data_sql):
        """ Module level set-up called once before any tests in this file are executed. Creates a temporary database
        and sets it up """

        global db, db_con, db_conf, skip_test

        if skip_test:
            self.skipTest("Skip BaseTest tests, it's a base class")

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

        with open(path_data_sql, 'r') as fh:
            lines_str = fh.read()

        with db_con.cursor() as cur:
            # Create the initial database structure (roles, schemas, tables etc.)
            # basically anything that doesn't change
            cur.execute(lines_str)

    def test_should_return15Items_when_getItemsToSend(self):
        self.prepareDB(path_data_sql='test/support/data/data_example.sql')

        dev_db = DeviceDB(
            db_config=db_conf,
            db_tablename=self.db_tablename
        )

        rows = dev_db.get_items_to_send(self.item_class)

        eq_(len(rows), 15)
        ok_(all(a.id <= b.id for a, b in zip(rows[:-1], rows[1:])))

    def test_should_returnZeroItems_when_getItemsToSend(self):
        self.prepareDB(path_data_sql='test/support/data/data_not_send.sql')

        dev_db = DeviceDB(
            db_config=db_conf,
            db_tablename=self.db_tablename
        )

        rows = dev_db.get_items_to_send(self.item_class)

        eq_(len(rows), 0)


class TestACMPlus(BaseDBGetItemsTests):
    item_class = ACMPlusItem
    db_tablename = "acmplus"


class TestPB200(BaseDBGetItemsTests):
    item_class = WIMDA
    db_tablename = "pb200"

#class TestNotification(BaseDBGetItemsTests):
#    item_class = Notification
#    db_tablename = "notification"

if __name__ == '__main__':
    unittest.main()
