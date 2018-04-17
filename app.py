import json
import logging
import logging.config
import multiprocessing
import os
import threading
import time

from dns_server import DNSServer


class Initializer:
    CONFIG_FILE = os.path.dirname(__file__) + '/config.json'

    def __init__(self):
        self._process_count = 0
        self._dns_server_ip = ''
        self._blacklist = []
        self._logger = logging.getLogger(__name__)
        self._reload_blacklist_interval = 0

    def start(self):
        self._setup()

        try:
            self._logger.info('Starting DNS Server')
            self._logger.debug(
                'made DnsServer with blacklist {}, process count {}, dns server ip {}'.format(list(self._blacklist),
                                                                                              self._process_count,
                                                                                              self._dns_server_ip))
            dns = DNSServer(blacklist_dns=self._blacklist, process_count=self._process_count,
                            dns_server_ip=self._dns_server_ip)

            threading.Thread(target=self._logger_thread, args=(dns.get_read_pipe(),)).start()
            threading.Thread(target=self._reload_blacklist).start()

            self._logger.debug('made dnsserver instance')
            try:
                dns.start_dns_server()
            except OSError:
                self._logger.fatal('Something happen', exc_info=True)
            finally:
                self._logger.info('Ended DNS Server')
        except Exception:
            self._logger.error('error!', exc_info=True)

    def _reload_blacklist(self):
        self._logger.debug('reload blacklst')
        while True:
            with open(self.CONFIG_FILE) as config_file:
                data = json.load(config_file)
            temp_blacklist = list(self._blacklist)
            for i in temp_blacklist:
                self._blacklist.remove(i)
            for i in data['blacklist']:
                self._blacklist.append(i)
            self._logger.info('blacklist has reloaded')
            self._logger.debug('current blacklist is {}'.format(self._blacklist))
            time.sleep(60)

    def _logger_thread(self, pipe):
        self._logger.debug('starting logger process')
        while True:
            try:
                record = pipe.recv()
                if record is None:
                    break
                self._logger.handle(record)
            except EOFError:
                pass

    def _setup(self):
        with open(self.CONFIG_FILE) as config_file:
            data = json.load(config_file)
        self._process_count = data['process_count']
        self._dns_server_ip = data['dns_server_ip']
        self._reload_blacklist_interval = data['reload_blacklist_interval']
        managed_list = multiprocessing.Manager().list()
        for i in data['blacklist']:
            managed_list.append(i)
        self._blacklist = managed_list
        logging.config.dictConfig(data['logging'])
        self._logger = logging.getLogger()


if __name__ == '__main__':
    Initializer().start()

