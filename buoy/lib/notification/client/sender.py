class DataSenderNamespaceClient(BaseNamespace, Sender):
    def __init__(self, io, path):
        BaseNamespace.__init__(self, io, path)
        Sender.__init__(self)
        self.queue_data = Queue()
        self.device_up = False
        self.active = True
        self.size = 100
        self.id = 1

    def on_connect(self):
        logger.info('[Connected]')

    def on_reconnect(self):
        logger.info('[Reconnected]')

    def on_disconnect(self):
        self.device_up = False
        logger.info('[Disconnected]')

    def on_device_up(self):
        self.device_up = True
        self.emit('get_data', self.size)

    def on_new_data(self, items):
        """ Envía los datos recibidos desde el dispositivo y envía la confirmación recibida
            desde el servidor al dispositivo, para que marque el dato como envíado """

        self.queue_data.put_nowait(items)

    def process_data(self):
        while self.active:
            items = self.queue_data.get()

            if not items:
                break

            items_ok = []
            items_error = []

            for item in items:
                logger.info('[New data]')
                try:
                    self.send_data(item)
                    items_ok.append(item)
                except Exception:
                    logger.info("Error")
                    items_ok.append(item)

            self.emit('sended_data', items_ok, items_error)

        self.active = False