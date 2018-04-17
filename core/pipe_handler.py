import logging.handlers
import multiprocessing
import logging


class PipeHandler(logging.Handler):
    def __init__(self, pipe: multiprocessing.Pipe):
        logging.Handler.__init__(self)
        self.pipe = pipe

    def emit(self, record: logging.LogRecord):
        try:
            self.pipe.send(record)
        except OSError:
            self.handleError(record)
