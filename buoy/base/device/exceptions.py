# -*- coding: utf-8 -*-

from datetime import datetime, timezone
from enum import IntEnum


class ExceptionLevel(IntEnum):
    LOW = 10
    NORMAL = 5
    HIGHT = 3
    CRITICAL = 1


class DeviceBaseException(Exception):
    def __init__(self, message, exception: Exception, level=ExceptionLevel.LOW, **kwargs):
        self.proccess = kwargs.pop('proccess', None)
        self.message = message
        self.level = level
        self.datetime = datetime.now(tz=timezone.utc)
        self.exception = exception


class ConnectionException(DeviceBaseException):
    def __init__(self, message, exception: Exception, level=ExceptionLevel.CRITICAL, **kwargs):
        super().__init__(message=message, exception=exception, level=level, **kwargs)


class LostConnectionException(DeviceBaseException):
    def __init__(self, exception: Exception, message="Lost your connection to the device",
                 level=ExceptionLevel.CRITICAL, **kwargs):
        super().__init__(message=message, exception=exception, level=level, **kwargs)


class DeviceNoDetectedException(DeviceBaseException):
    def __init__(self, exception: Exception, message="Device no detected", level=ExceptionLevel.CRITICAL, **kwargs):
        super().__init__(message=message, exception=exception, level=level, **kwargs)


class ProcessDataExecption(DeviceBaseException):
    def __init__(self, exception: Exception, message="Error processed data",
                 level=ExceptionLevel.CRITICAL, **kwargs):
        super().__init__(message=message, exception=exception, level=level, **kwargs)
