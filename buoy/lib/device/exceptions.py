# -*- coding: utf-8 -*-

from datetime import datetime, timezone
from buoy.lib.notification.common import NotificationLevel


class DeviceBaseException(Exception):
    def __init__(self, message, exception: Exception, level=NotificationLevel.LOW, **kwargs):
        self.proccess = kwargs.pop('proccess', None)
        self.message = message
        self.level = level
        self.datetime = datetime.now(tz=timezone.utc)
        self.exception = exception


class ConnectionException(DeviceBaseException):
    def __init__(self, message, exception: Exception, level=NotificationLevel.CRITICAL, **kwargs):
        super().__init__(message=message, exception=exception, level=level, **kwargs)


class LostConnectionException(DeviceBaseException):
    def __init__(self, exception: Exception, message="Lost your connection to the device",
                 level=NotificationLevel.CRITICAL, **kwargs):
        super().__init__(message=message, exception=exception, level=level, **kwargs)


class DeviceNoDetectedException(DeviceBaseException):
    def __init__(self, exception: Exception, message="Device no detected", level=NotificationLevel.CRITICAL, **kwargs):
        super().__init__(message=message, exception=exception, level=level, **kwargs)