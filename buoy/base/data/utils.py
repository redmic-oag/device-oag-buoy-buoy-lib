from datetime import timedelta

UNITS = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days", "w": "weeks"}


def convert_to_seconds(s):
    if isinstance(s, int):
        # We are dealing with a raw number
        return s

    try:
        seconds = int(s)
        # We are dealing with an integer string
        return seconds
    except ValueError:
        # We are dealing with some other string or type
        pass

    # Expecting a string ending in [m|h|d|s|w]
    count = int(s[:-1])
    unit = UNITS[s[-1]]
    td = timedelta(**{unit: count})
    return td.seconds + 60 * 60 * 24 * td.days


def round_time(dt=None, round_to=1, to='average'):
    seconds = (dt - dt.min).seconds

    if seconds % round_to == 0:
        rounding = (seconds + round_to / 2) // round_to * round_to
    else:
        if to == 'up':
            rounding = (seconds + round_to) // round_to * round_to
        elif to == 'down':
            rounding = seconds // round_to * round_to
        else:
            rounding = (seconds + round_to / 2) // round_to * round_to

    return dt + timedelta(0, rounding - seconds, -dt.microsecond)
