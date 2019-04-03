import unittest
from datetime import datetime, timezone
from os import path

from nose.tools import eq_, ok_

from buoy.base.database import DeviceDB
from buoy.tests.database import *
from buoy.tests.item import Item


class BaseDBTests(unittest.TestCase):
    item_class = None
    db_tablename = None
    db_cls = DeviceDB
    skip_test = False
    path_sql = 'tests/support/data'

    @classmethod
    def setUpClass(cls):
        global skip_test

        if cls is BaseDBTests:
            skip_test = True
        else:
            skip_test = False

        super(BaseDBTests, cls).setUpClass()

    def setUp(self):
        """ Module level set-up called once before any tests in this file are executed. Creates a temporary database
        and sets it up """

        if skip_test:
            self.skipTest("Skip BaseTest tests, it's a base class")

        global db_conf

        db_conf = prepare_db(path.join(self.path_sql, 'setup.sql'))

    def tearDown(self):
        """ Called after all of the tests in this file have been executed to close the database connecton and destroy
        the temporary database """

        close_db()

    def test_add_item_in_db(self):

        item_to_insert = self.item_class(**self.data)

        dev_db = self.db_cls(
            db_config=db_conf,
            db_tablename=self.db_tablename,
            cls_item=self.item_class
        )

        item = dev_db.save(item_to_insert)

        rows = apply_sql_clause("""SELECT * FROM %s""" % (self.db_tablename,))

        eq_(len(rows), 1)
        row = rows[0]

        if not hasattr(self, "data_expected"):
            self.data_expected = self.data

        for key, value in self.data_expected.items():
            eq_(row[key], value)

        eq_(row['uuid'], item.uuid)

    def test_update_status_items_in_db(self):

        dev_db = self.db_cls(
            db_config=db_conf,
            db_tablename=self.db_tablename,
            cls_item=self.item_class
        )

        sql_clause = """SELECT * FROM %s ORDER BY date""" % (self.db_tablename,)
        before_rows = apply_sql_clause(sql_clause)

        uuids = list()
        for row in before_rows:
            uuids.append(row['uuid'])
        dev_db.update_status(uuids)

        after_rows = apply_sql_clause(sql_clause)

        for idx, aft_row in enumerate(after_rows):
            eq_(aft_row['sent'], True)
            ok_(aft_row['uuid'] == before_rows[idx]['uuid'])
            ok_(aft_row['num_attempts'] > before_rows[idx]['num_attempts'])

    def test_should_return15Items_when_getItemsToSend(self):
        apply_sql_file(path.join(self.path_sql, 'data_example.sql'))
        dev_db = self.db_cls(
            db_config=db_conf,
            db_tablename=self.db_tablename,
            cls_item=self.item_class
        )
        rows = dev_db.get_items_to_send()

        eq_(len(rows), 15)
        ok_(all(a.date <= b.date for a, b in zip(rows[:-1], rows[1:])))

    def test_should_returnZeroItems_when_getItemsToSend(self):
        apply_sql_file(path.join(self.path_sql, 'data_not_send.sql'))

        dev_db = self.db_cls(
            db_config=db_conf,
            db_tablename=self.db_tablename,
            cls_item=self.item_class
        )

        rows = dev_db.get_items_to_send()

        eq_(len(rows), 0)


class TestDeviceDB(BaseDBTests):
    item_class = Item
    db_tablename = "device"
    data = {
        'date': datetime.now(tz=timezone.utc),
        'value': 30.3273
    }


if __name__ == '__main__':
    unittest.main()
