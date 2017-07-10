INSERT INTO acmplus (id, datetime, vx, vy, speed, direction, water_temperature, sended, num_attempts) VALUES
    (1, '2017-01-23 13:43:48', 19.57, 69.24, 71.9525016938258, 15.7824191508417, 24.1, true, 0),
    (2, '2017-01-23 13:45:39', 20.04, 68.62, 71.4864043017971, 16.2800817097405, 24.11, false, 3),
    (3, '2017-01-23 13:46:39', 20.18, 68.7, 71.6025306815339, 16.3696710544201, 24.11, true, 0),
    (4, '2017-01-23 14:05:21', 19.86, 68.53, 71.3497056756368, 16.1615928761929, 24.14, false, 3);

INSERT INTO pb200 (id, datetime, barometric_pressure_inch, barometric_pressure_bar, air_temperature,
        water_temperature, relative_humidity, absolute_humidity, dew_point, wind_direction_true,
        wind_direction_magnetic, wind_speed_knots, wind_speed_meters, sended, num_attempts) VALUES
    (1, '2017-02-17 07:00:01.667227', 30.3273, 1.027, 26.8, 20.1, 12.3, 21, 2.3, 2, 128.7, 134.6, 0.3, false, 3),
    (2, '2017-02-17 07:01:02.667227', 30.3273, 1.027, 26.8, 20.1, 12.3, 21, 2.3, 2, 128.7, 134.6, 0.3, false, 3),
    (3, '2017-02-17 07:01:04.099031', 30.3273, 1.027, 26.8, 20.1, 12.3, 21, 2.3, 2, 128.7, 134.6, 0.3, true, 0),
    (4, '2017-02-17 07:01:21.657981', 30.3273, 1.027, 26.8, 20.1, 12.3, 21, 2.3, 2, 128.7, 134.6, 0.3, false, 3);
    

INSERT INTO notification (id, datetime, level, phone, message, sended, type, num_attempts) VALUES
    (1, '2017-06-22 11:12:44.464156+01', 1, null, 'Device no detected', true, 1, 0),
    (2, '2017-06-22 11:12:44.44309+01', 3, null, 'Start service current-meter', true, 1, 0),
    (3, '2017-06-22 11:12:44.466089+01', 3, null, 'Error in service current-meter', true, 1, 0),
    (4, '2017-06-22 13:10:50.954155+01', 3, null, 'Error in service current-meter', false, 1, 3);