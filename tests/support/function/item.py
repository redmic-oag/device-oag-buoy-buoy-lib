from datetime import datetime, timezone

from buoy.base.data.item import BaseItem


class Item(BaseItem):
    def __init__(self, **kwargs):
        self.value = kwargs.pop('value', None)
        super(Item, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = self._convert_string_to_decimal(value)


def get_item():
    data = {
        'date': datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        'value': '26.8'
    }
    return Item(**data)


def get_items(num=2):
    items = []
    for i in range(0, num):
        items.append(get_item())
    return items
