import logging.handlers


class PipeHandler(logging.Handler):
    def __init__(self, pipe):
        logging.Handler.__init__(self)
        self.pipe = pipe

    def emit(self, record):
        try:
            self.pipe.send(record)
        except OSError:
            self.handleError(record)
