# -*- coding: utf-8 -*-

from buoy.lib.protocol.item import BaseItem


class WIMDA(BaseItem):
    def __init__(self, **kwargs):
        BaseItem.__init__(self, **kwargs)

        self.barometric_pressure_inch = kwargs.pop('barometric_pressure_inch', None)
        self.barometric_pressure_bar = kwargs.pop('barometric_pressure_bar', None)
        self.air_temperature = kwargs.pop('air_temperature', None)
        self.water_temperature = kwargs.pop('water_temperature', None)
        self.relative_humidity = kwargs.pop('relative_humidity', None)
        self.absolute_humidity = kwargs.pop('absolute_humidity', None)
        self.dew_point = kwargs.pop('dew_point', None)
        self.wind_direction_true = kwargs.pop('wind_direction_true', None)
        self.wind_direction_magnetic = kwargs.pop('wind_direction_magnetic', None)
        self.wind_speed_knots = kwargs.pop('wind_speed_knots', None)
        self.wind_speed_meters = kwargs.pop('wind_speed_meters', None)

    @staticmethod
    def from_nmea(in_datetime, wimda):
        return WIMDA(
            datetime=in_datetime,
            barometric_pressure_inch=wimda.b_pressure_inch,
            barometric_pressure_bar=wimda.b_pressure_bar,
            air_temperature=wimda.air_temp,
            water_temperature=wimda.water_temp,
            relative_humidity=wimda.rel_humidity,
            absolute_humidity=wimda.abs_humidity,
            dew_point=wimda.dew_point,
            wind_direction_true=wimda.direction_true,
            wind_direction_magnetic=wimda.direction_magnetic,
            wind_speed_knots=wimda.wind_speed_knots,
            wind_speed_meters=wimda.wind_speed_meters)

    @property
    def barometric_pressure_inch(self):
        """
        :return: Barometric pressure, inches of mercury
        :rtype: Decimal
        """
        return self._barometric_pressure_inch

    @barometric_pressure_inch.setter
    def barometric_pressure_inch(self, value):
        self._barometric_pressure_inch = self._convert_string_to_decimal(value)

    @property
    def barometric_pressure_bar(self):
        """
        :return: Barometric pressure, bars
        :rtype: Decimal
        """
        return self._barometric_pressure_bar

    @barometric_pressure_bar.setter
    def barometric_pressure_bar(self, value):
        self._barometric_pressure_bar = self._convert_string_to_decimal(value)

    @property
    def air_temperature(self):
        """
        :return: Barometric pressure, bars
        :rtype: Decimal
        """
        return self._air_temperature

    @air_temperature.setter
    def air_temperature(self, value):
        self._air_temperature = self._convert_string_to_decimal(value)

    @property
    def water_temperature(self):
        """
        :return: Water temperature, degrees Celsius
        :rtype: Decimal
        """
        return self._water_temperature

    @water_temperature.setter
    def water_temperature(self, value):
        self._water_temperature = self._convert_string_to_decimal(value)

    @property
    def relative_humidity(self):
        """
        :return: Relative humidity, percent
        :rtype: Decimal
        """
        return self._relative_humidity

    @relative_humidity.setter
    def relative_humidity(self, value):
        self._relative_humidity = self._convert_string_to_decimal(value)

    @property
    def absolute_humidity(self):
        """
        :return: Absolute humidity, percent
        :rtype: Decimal
        """
        return self._absolute_humidity

    @absolute_humidity.setter
    def absolute_humidity(self, value):
        self._absolute_humidity = self._convert_string_to_decimal(value)

    @property
    def dew_point(self):
        """
        :return: Dew point, degrees C
        :rtype: Decimal
        """
        return self._dew_point

    @dew_point.setter
    def dew_point(self, value):
        self._dew_point = self._convert_string_to_decimal(value)

    @property
    def wind_direction_true(self):
        """
        :return: Wind direction true
        :rtype: Decimal
        """
        return self._wind_direction_true

    @wind_direction_true.setter
    def wind_direction_true(self, value):
        self._wind_direction_true = self._convert_string_to_decimal(value)

    @property
    def wind_direction_magnetic(self):
        """
        :return: Wind direction magnetic
        :rtype: Decimal
        """
        return self._wind_direction_magnetic

    @wind_direction_magnetic.setter
    def wind_direction_magnetic(self, value):
        self._wind_direction_magnetic = self._convert_string_to_decimal(value)

    @property
    def wind_speed_knots(self):
        """
        :return: Wind speed knots
        :rtype: Decimal
        """
        return self._wind_speed_knots

    @wind_speed_knots.setter
    def wind_speed_knots(self, value):
        self._wind_speed_knots = self._convert_string_to_decimal(value)

    @property
    def wind_speed_meters(self):
        """
        :return: Wind speed meters/second
        :rtype: Decimal
        """
        return self._wind_speed_meters

    @wind_speed_meters.setter
    def wind_speed_meters(self, value):
        self._wind_speed_meters = self._convert_string_to_decimal(value)

    def __str__(self):
        return ("Id: {id}\n"
                "Datetime: {datetime}\n"
                "Barometric pressure: {barometric_pressure_inch} in - {barometric_pressure_bar} bar\n"
                "Air temperature: {air_temperature} ºC\n"
                "Water temperature: {water_temperature} ºC\n"
                "Relative humidity: {relative_humidity} %\n"
                "Absolute humidity: {absolute_humidity} %\n"
                "Dew point: {dew_point} C\n"
                "Wind direction true: {wind_direction_true} º\n"
                "Wind direction magnetic: {wind_direction_magnetic} º\n"
                "Wind speed: {wind_speed_knots} knots - {wind_speed_meters} m/s").format(**dict(self))
