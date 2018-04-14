import json
import logging
import logging.config
import os
import threading

from dns_server import DNSServer


class Initializer:
    CONFIG_FILE = os.path.dirname(__file__) + '/config.json'

    def __init__(self):
        self._process_count = 0
        self._dns_server_ip = ''
        self._blacklist = []
        self._logger = logging.getLogger(__name__)

    def start(self):
        self._setup()
        try:
            self._logger.info('Starting DNS Server')
            self._logger.debug(
                'made DnsServer with blacklist {0}, process count {1}, dns server ip {2}'.format(str(self._blacklist),
                                                                                                 self._process_count,
                                                                                                 self._dns_server_ip))
            dns = DNSServer(blacklist_dns=self._blacklist, process_count=self._process_count,
                            dns_server_ip=self._dns_server_ip)

            threading.Thread(target=self._logger_thread, args=(dns.get_read_pipe(),)).start()

            self._logger.debug('made dnsserver instance')
            try:
                dns.start_dns_server()
            except OSError:
                self._logger.error('Something happen', exc_info=True)

        except Exception:
            self._logger.error('error!', exc_info=True)

    def _logger_thread(self, pipe):
        self._logger.debug('starting logger process')
        while True:
            record = pipe.recv()
            if record is None:
                break
            self._logger.handle(record)

    def _setup(self):
        with open(self.CONFIG_FILE) as config_file:
            data = json.load(config_file)
        self._process_count = data['process_count']
        self._dns_server_ip = data['dns_server_ip']
        self._blacklist = data['blacklist']
        logging.config.dictConfig(data['logging'])
        self._logger = logging.getLogger()


if __name__ == '__main__':
    Initializer().start()
