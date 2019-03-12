# -*- coding: utf-8 -*-

from queue import Queue, Empty
from threading import Thread

from paho.mqtt.client import *

from buoy.base.data.item import ItemQueue, Status
from buoy.base.device.threads.base import BaseThread

logger = logging.getLogger(__name__)


class Limbo(object):
    def __init__(self):
        self.items = dict()

    def add(self, id, item):
        logger.debug("Add item %s with id %s to limbo" % (item, id,))
        self.items[id] = item

    def clear(self):
        self.items.clear()

    def get(self, id):
        if self.exists(id):
            return self.items[id]
        return None

    def pop(self, id):
        item = self.get(id)
        if item:
            del self.items[id]
        logger.debug("Remove item %s with id %s to limbo" % (item, id,))
        return item

    def size(self):
        return len(self.items)

    def exists(self, id):
        return id in self.items


def loop(client):
    client.loop_start()


class MqttThread(BaseThread):
    """
    Clase base encargada de enviar los datos al servidor
    """

    def __init__(self, queue_send_data: Queue, queue_data_sent: Queue, queue_notice: Queue, **kwargs):
        super(MqttThread, self).__init__(queue_notice)

        self.queue_send_data = queue_send_data
        self.queue_data_sent = queue_data_sent
        self.queue_notice = queue_notice
        self.__connected_to_mqtt = False
        self.attemp_connect = False
        self.thread_mqtt = None

        self.client_id = kwargs.pop("client_id", "")
        self.clean_session = kwargs.pop("clean_session", True)
        self.protocol = MQTTv311
        self.transport = kwargs.pop("transport", "tcp")

        self.broker_url = kwargs.pop("broker_url", "iot.eclipse.org")
        self.broker_port = kwargs.pop("broker_port", 1883)
        self.topic_data = kwargs.pop("topic_data", "buoy")
        self.keepalive = kwargs.pop("keepalive", 60)
        self.reconnect_delay = kwargs.pop("reconnect_delay", {"min_delay": 1, "max_delay": 120})

        self.client = MqttClient(client_id=self.client_id, protocol=self.protocol, clean_session=self.clean_session)

        self.limbo = Limbo()

        if "username" in kwargs:
            self.username = kwargs.pop("username", "username")
            self.password = kwargs.pop("password", None)
            self.client.username_pw_set(self.username, self.password)

        self.qos = kwargs.pop("qos", 0)

    def before_activity(self):
        self.connect_to_mqtt()

    def connect_to_mqtt(self):
        logger.info("Try to connect to broker")
        self.client.connect(host=self.broker_url, port=self.broker_port, keepalive=self.keepalive)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish

        self.thread_mqtt = Thread(target=loop, args=(self.client,))
        self.thread_mqtt.start()

    def activity(self):
        if self.is_connected_to_mqtt():
            try:
                item = self.queue_send_data.get_nowait()
                self.send(item)
                self.queue_send_data.task_done()
            except Empty:
                logger.debug("No data for sending to broker")
                pass

    def is_connected_to_mqtt(self):
        return self.__connected_to_mqtt

    def send(self, item):
        """

        :param item:
        """
        json = str(item.to_json())
        logger.info("Publish data '%s' to topic '%s'" % (self.topic_data, json))
        try:
            self.limbo.add(item.uuid, item)
            self.client.publish(self.topic_data, json, qos=self.qos, mid=item.uuid)
        except ValueError:
            logger.warning("Can't sent item", exc_info=True)
            self.limbo.pop(item.uuid)
            self.queue_data_sent.put_nowait(ItemQueue(data=item, status=Status.FAILED))
            pass

    def stop(self):
        logger.info("Disconnecting to broker")
        self.client.disconnect()

    def on_publish(self, client, userdata, mid):
        """
        Callback del método publish, si se entra aquí significa que el item fue
        enviado al broker correctamente

        :param client:
        :param userdata:
        :param mid:
        """
        if self.limbo.exists(mid):
            item = self.limbo.pop(mid)
            logger.debug("Update item in db %s", item.uuid)
            self.queue_data_sent.put_nowait(ItemQueue(data=item, status=Status.SENT))
        else:
            logger.warning("Item isn't in limbo")

    def on_connect(self, client, userdata, flags, rc):
        """
        :param client:
        :param userdata:
        :param flags:
        :param rc:
        """
        if rc == 0:
            logger.info("Connected to broker %s with client_id %s", self.broker_url, client)
            self.__connected_to_mqtt = True
            if flags["session present"]:
                logger.info("Connected to broker using existing session")
            else:
                logger.info("Connected to broker using clean session")
        else:
            self.__connected_to_mqtt = False
            if rc == 1:
                logger.error("Connection refused - incorrect protocol version")
            elif rc == 2:
                logger.error("Connection refused - invalid client identifier")
            elif rc == 3:
                logger.error("Connection refused - server unavailable")
            elif rc == 4:
                logger.error("Connection refused - bad username or password")
            elif rc == 5:
                logger.error("Connection refused - not authorised")
            else:
                logger.error("Error connected to broker")

    def on_disconnect(self, client, userdata, rc):
        """

        :param client:
        :param userdata:
        :param rc:
        """
        self.__connected_to_mqtt = False
        self.limbo.clear()
        if rc != 0:
            logger.error("Unexpected disconnection to broker")
        else:
            client.loop_stop()
            super().stop()
        logger.info("Disconnected to broker with result code %s" % str(rc))


try:
    import ssl
except ImportError:
    ssl = None


class MqttClient(Client):
    def __init__(self, client_id="", clean_session=True, userdata=None,
                 protocol=MQTTv311, transport="tcp"):
        super(MqttClient, self).__init__(client_id=client_id, clean_session=clean_session,
                                         userdata=userdata, protocol=protocol, transport=transport)

    def publish(self, topic, payload=None, qos=0, retain=False, mid=None):
        """Publish a message on a topic.

        This causes a message to be sent to the broker and subsequently from
        the broker to any clients subscribing to matching topics.

        topic: The topic that the message should be published on.
        payload: The actual message to send. If not given, or set to None a
        zero length message will be used. Passing an int or float will result
        in the payload being converted to a string representing that number. If
        you wish to send a true int/float, use struct.pack() to create the
        payload you require.
        qos: The quality of service level to use.
        retain: If set to true, the message will be set as the "last known
        good"/retained message for the topic.

        Returns a MQTTMessageInfo class, which can be used to determine whether
        the message has been delivered (using info.is_published()) or to block
        waiting for the message to be delivered (info.wait_for_publish()). The
        message ID and return code of the publish() call can be found at
        info.mid and info.rc.

        For backwards compatibility, the MQTTMessageInfo class is iterable so
        the old construct of (rc, mid) = client.publish(...) is still valid.

        rc is MQTT_ERR_SUCCESS to indicate success or MQTT_ERR_NO_CONN if the
        client is not currently connected.  mid is the message ID for the
        publish request. The mid value can be used to track the publish request
        by checking against the mid argument in the on_publish() callback if it
        is defined.

        A ValueError will be raised if topic is None, has zero length or is
        invalid (contains a wildcard), if qos is not one of 0, 1 or 2, or if
        the length of the payload is greater than 268435455 bytes."""
        if topic is None or len(topic) == 0:
            raise ValueError('Invalid topic.')

        topic = topic.encode('utf-8')

        if self._topic_wildcard_len_check(topic) != MQTT_ERR_SUCCESS:
            raise ValueError('Publish topic cannot contain wildcards.')

        if qos < 0 or qos > 2:
            raise ValueError('Invalid QoS level.')

        if isinstance(payload, unicode):
            local_payload = payload.encode('utf-8')
        elif isinstance(payload, (bytes, bytearray)):
            local_payload = payload
        elif isinstance(payload, (int, float)):
            local_payload = str(payload).encode('ascii')
        elif payload is None:
            local_payload = b''
        else:
            raise TypeError('payload must be a string, bytearray, int, float or None.')

        if len(local_payload) > 268435455:
            raise ValueError('Payload too large.')

        if mid:
            local_mid = mid
        else:
            local_mid = self._mid_generate()

        if qos == 0:
            info = MQTTMessageInfo(local_mid)
            rc = self._send_publish(local_mid, topic, local_payload, qos, retain, False, info)
            info.rc = rc
            return info
        else:
            message = MQTTMessage(local_mid, topic)
            message.timestamp = time_func()
            message.payload = local_payload
            message.qos = qos
            message.retain = retain
            message.dup = False

            with self._out_message_mutex:
                if self._max_queued_messages > 0 and len(self._out_messages) >= self._max_queued_messages:
                    message.info.rc = MQTT_ERR_QUEUE_SIZE
                    return message.info

                if local_mid in self._out_messages:
                    message.info.rc = MQTT_ERR_QUEUE_SIZE
                    return message.info

                self._out_messages[message.mid] = message
                if self._max_inflight_messages == 0 or self._inflight_messages < self._max_inflight_messages:
                    self._inflight_messages += 1
                    if qos == 1:
                        message.state = mqtt_ms_wait_for_puback
                    elif qos == 2:
                        message.state = mqtt_ms_wait_for_pubrec

                    rc = self._send_publish(message.mid, topic, message.payload, message.qos, message.retain,
                                            message.dup)

                    # remove from inflight messages so it will be send after a connection is made
                    if rc is MQTT_ERR_NO_CONN:
                        self._inflight_messages -= 1
                        message.state = mqtt_ms_publish

                    message.info.rc = rc
                    return message.info
                else:
                    message.state = mqtt_ms_queued
                    message.info.rc = MQTT_ERR_SUCCESS
                    return message.info
