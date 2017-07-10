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


class BaseDBUpdateStatusTests(unittest.TestCase):
    item_class = None
    db_tablename = None

    @classmethod
    def setUpClass(cls):
        if cls is BaseDBUpdateStatusTests:
            raise unittest.SkipTest("Skip BaseTest tests, it's a base class")
        super(BaseDBUpdateStatusTests, cls).setUpClass()

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

        with open('test/support/data/data_example.sql', 'r') as fh:
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

    def test_update_status_items_in_db(self):

        dev_db = DeviceDB(
            db_config=db_conf,
            db_tablename=self.db_tablename
        )

        with db_con.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""SELECT * FROM %s ORDER BY id""" % (self.db_tablename,))
            before_rows = cur.fetchall()

        ids = list(range(1, 22))
        dev_db.update_status(ids)

        with db_con.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""SELECT * FROM %s ORDER BY id""" % (self.db_tablename,))
            after_rows = cur.fetchall()

        for idx, aft_row in enumerate(after_rows):
            eq_(aft_row['sended'], True)
            ok_(aft_row['id'] == before_rows[idx]['id'])
            ok_(aft_row['num_attempts'] > before_rows[idx]['num_attempts'])


class TestACMPlus(BaseDBUpdateStatusTests):
    item_class = ACMPlusItem
    db_tablename = "acmplus"


class TestPB200(BaseDBUpdateStatusTests):
    item_class = WIMDA
    db_tablename = "pb200"

if __name__ == '__main__':
    unittest.main()
