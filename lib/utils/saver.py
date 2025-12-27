from kivy.clock import Clock


class Saver:
    def __init__(self, storage = None, timeout = 1, **kwargs):
        super().__init__(**kwargs)  # Continue the MRO chain
        self.events  = {}
        self.timeout = timeout
        self.storage = {} if storage is None else storage

    def schedule_save(self, id, key, value):
        if self.events.get(id):
            self.events[id].cancel()

        self.events[id] = Clock.schedule_once(lambda dt: self.instant_save(key, value), self.timeout)

    def instant_save(self, key, value):
        try:
            if isinstance(self.storage, dict):
                self.storage.update({key: value})
                print('[SAVER]', f'{key} inserted into the in-memory dict storage: {value}')
                print('[SAVER]', 'Setting change will be lost when app closes')
            else:
                if isinstance(value, dict):
                    self.storage.put(key, **value)
                else:
                    self.storage.put(key, value = value)
                    self.storage.store_sync()  # Force write to disk
                print('[SAVER]', f'{key} inserted into the storage: {value}')

        except Exception as e:
            print('[SAVER]', f'Storage error: {e}')
