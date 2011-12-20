from sockjs.tornado.transports import pollingbase


class StreamingTransportBase(pollingbase.PollingTransportBase):
    def initialize(self, server):
        super(StreamingTransportBase, self).initialize(server)

        self.amount_limit = self.server.settings['response_limit']

    def should_finish(self, data_len):
        self.amount_limit -= data_len

        if self.amount_limit <= 0:
            return True
