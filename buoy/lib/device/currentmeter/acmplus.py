# -*- coding: utf-8 -*-

import math

from buoy.lib.protocol.item import BaseItem


class ACMPlusItem(BaseItem):
    def __init__(self, **kwargs):
        BaseItem.__init__(self, **kwargs)
        self.vx = kwargs.pop('vx', None)
        self.vy = kwargs.pop('vy', None)
        self.speed = kwargs.pop('speed', None)
        self.direction = kwargs.pop('direction', None)
        self.water_temperature = kwargs.pop('water_temperature', None)

    @property
    def vx(self):
        """
        :return: The X component of the current velocity in cm/sec relative to the direction indicator arrow on the
                 velocity head of instrument
        :rtype: Decimal
        """
        return self._vx

    @vx.setter
    def vx(self, value):
        self._vx = self._convert_string_to_decimal(value)

    @property
    def vy(self):
        """
        :return: The Y component of the current velocity in cm/sec relative to the direction indicator arrow on the
                 velocity head of instrument
        :rtype: Decimal
        """
        return self._vy

    @vy.setter
    def vy(self, value):
        self._vy = self._convert_string_to_decimal(value)

    @property
    def speed(self):
        if not self._speed and self.is_fulled:
            self._speed = math.sqrt(math.pow(self._vx, 2) + math.pow(self._vy, 2))

        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = self._convert_string_to_decimal(value)

    @property
    def direction(self):
        if not self._direction and self.is_fulled:
            dir_current = math.degrees(math.atan2(self.vy, self.vx))
            if (self.vy >= 0) and (self.vx >= 0):  # Cuadrante entre 0º y 90º
                dir_current = 90 - dir_current
            elif (self.vy <= 0) and (self.vx >= 0):  # Cuadrante entre 90º y 180º
                dir_current = math.fabs(dir_current) + 90
            elif (self.vy <= 0) and (self.vx <= 0):  # Cuadrante entre 180º y 270º
                dir_current = math.fabs(dir_current) + 90
            elif (self.vy >= 0) and (self.vx <= 0):  # Cuadrante entre 270º y 360º
                dir_current = 360 - (dir_current - 90)

            self.direction = dir_current

        return self._direction

    @direction.setter
    def direction(self, value):
        self._direction = self._convert_string_to_decimal(value)

    @property
    def water_temperature(self):
        """
        :return: The water temperature in °C
        :rtype: Decimal
        """
        return self._water_temperature

    @water_temperature.setter
    def water_temperature(self, value):
        self._water_temperature = self._convert_string_to_decimal(value)

    def is_fulled(self):
        return self._vx and self._vy
