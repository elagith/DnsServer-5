import logging
import logging.config
import multiprocessing
import os
import socket
from multiprocessing import Pipe

from .dns_worker import DNSWorker


class DNSServer:
    CONFIG_FILE = os.path.dirname(__file__) + '/config.json'

    _LOCAL_IP = '127.0.0.1'
    _DNS_PORT = 53

    def __init__(self, blacklist_dns=None, process_count=1, dns_server_ip='1.1.1.1'):
        self._logger = None
        if blacklist_dns is None:
            blacklist_dns = []
        self._PROCESS_COUNT = process_count
        self._DNS_SERVER_IP = dns_server_ip
        self._BLACKLIST_DNS = blacklist_dns
        self._reader, self._writer = Pipe(duplex=False)

    def start_dns_server(self):
        self.setup_worker()
        self._logger.debug('finish to setup the worker')
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as localhost_socket:
            dns_processes = []
            localhost_socket.bind((self._LOCAL_IP, self._DNS_PORT))
            self._logger.info('bind to localhost!')
            self._logger.debug('process count - {0}'.format(self._PROCESS_COUNT))
            for i in range(self._PROCESS_COUNT):
                dns_worker = DNSWorker(self._BLACKLIST_DNS, self._DNS_SERVER_IP, localhost_socket, self._writer)
                multiprocessing.Process(target=dns_worker.start_worker, args=()).start()
                dns_processes.append(dns_worker)

    def setup_worker(self):
        self._logger = logging.getLogger()

    def get_read_pipe(self):
        return self._reader


