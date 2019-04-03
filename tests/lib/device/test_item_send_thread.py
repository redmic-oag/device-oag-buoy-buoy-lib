from queue import Queue
from unittest.mock import MagicMock

from nose.tools import ok_

from buoy.base.data.item import Status
from buoy.base.database import DeviceDB
from buoy.base.device.threads.mqtt import MqttThread, MQTT_ERR_SUCCESS
from buoy.tests.base_device_tests import *
from buoy.tests.item import *


class FakeDeviceDB(DeviceDB):
    def __init__(self):
        pass


class FakeReponseMQTT(object):
    def __init__(self, rc=0, mid=1):
        self.rc = rc
        self.mid = mid

    def wait_for_publish(self):
        pass


class FakeMQTT(object):
    def __init__(self):
        pass

    def disconnect(self):
        pass


class TestMqttThread(unittest.TestCase):
    def setUp(self):
        self.cls = Item
        self.topic = "redmic/data"
        self.qos = 1
        self.thread = MqttThread(db=FakeDeviceDB(), queue_send_data=Queue(), queue_data_sent=Queue(),
                                 queue_notice=Queue())

    def fill_limbo(self, size):
        items = get_items(size)
        for idx, item in enumerate(items):
            self.thread.limbo.add(idx, item)

    @patch.object(MqttThread, 'is_connected_to_mqtt', return_value=False)
    @patch.object(MqttThread, 'send')
    def test_onceCallToConnectMqtt_when_inititializeThread(self, mock_send, mock_is_connected_to_mqtt):
        self.thread.activity()

        eq_(mock_is_connected_to_mqtt.call_count, 1)
        eq_(mock_send.call_count, 0)

    def test_deleteItemInLimbo_when_itemSuccessPublished(self):
        self.fill_limbo(size=2)

        self.thread.on_publish(None, None, 1)

        eq_(self.thread.limbo.size(), 1)
        ok_(self.thread.limbo.get(1) is None)

    def test_isConnectIsTrue_when_onConnectCallbackReceiveRCEqualZero(self):
        self.fill_limbo(size=2)

        self.thread.on_connect(None, None, flags={"session present": 1}, rc=0)

        ok_(self.thread.is_connected_to_mqtt())

    def test_isConnectIsFalse_when_onConnectCallbackReceiveRcDistinctZero(self):
        self.fill_limbo(size=2)

        self.thread.on_connect(None, None, None, rc=1)

        ok_(self.thread.is_connected_to_mqtt() is False)

    def test_clearLimboAndStopThread_when_disconnectMqttOk(self):
        self.fill_limbo(size=2)
        self.thread.active = True
        client = FakeMQTT()
        client.loop_stop = MagicMock()

        self.thread.on_disconnect(client, None, 0)

        ok_(self.thread.is_connected_to_mqtt() is False)
        ok_(self.thread.is_active() is False)
        eq_(self.thread.limbo.size(), 0)

    def test_clearLimboAndDontStopThread_when_disconnectMqttKO(self):
        self.fill_limbo(size=2)
        self.thread.active = True
        client = FakeMQTT()

        self.thread.on_disconnect(client, None, 1)

        ok_(self.thread.is_connected_to_mqtt() is False)
        ok_(self.thread.is_active() is True)
        eq_(self.thread.limbo.size(), 0)

    def test_itemInsideLimbo_when_sendItem(self):
        item_expected = get_item()
        mid = item_expected.uuid
        client = FakeMQTT()
        client.publish = MagicMock(return_value=FakeReponseMQTT(rc=MQTT_ERR_SUCCESS, mid=mid))
        self.thread.client = client

        self.thread.send(item_expected)

        eq_(self.thread.limbo.size(), 1)
        eq_(self.thread.limbo.get(mid), item_expected)

    def test_limboIsEmpty_when_failedSentItem(self):
        item_expected = get_item()
        client = FakeMQTT()
        client.publish = MagicMock(side_effect=ValueError('Error sent item'))
        self.thread.client = client

        self.thread.send(item_expected)

        eq_(self.thread.queue_data_sent.qsize(), 1)
        item = self.thread.queue_data_sent.get_nowait()
        eq_(item_expected, item.data)
        ok_(item.status == Status.FAILED)
        eq_(self.thread.limbo.size(), 0)


if __name__ == '__main__':
    unittest.main()
