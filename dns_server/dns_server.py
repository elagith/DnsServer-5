import logging
import logging.config
import multiprocessing
import os
import socket

from .dns_worker import DNSWorker


class DNSServer:
    CONFIG_FILE = '{}/config.json'.format(os.path.dirname(__file__))

    _LOCAL_IP = '127.0.0.1'
    _DNS_PORT = 53

    def __init__(self, blacklist_dns: [str] = [], process_count: int = 1, dns_server_ip: str = '1.1.1.1'):
        self._logger = None
        self._PROCESS_COUNT = process_count
        self._DNS_SERVER_IP = dns_server_ip
        self._BLACKLIST_DNS = blacklist_dns
        self._queue =multiprocessing.Queue()


    def start_dns_server(self):
        self._setup_worker()
        self._logger.debug('finish to setup the worker')
        dns_processes = []
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as localhost_socket:
                localhost_socket.bind((self._LOCAL_IP, self._DNS_PORT))
                self._logger.info('bind to localhost on port {}'.format(self._DNS_PORT))
                self._logger.debug('process count - {0}'.format(self._PROCESS_COUNT))
                for i in range(self._PROCESS_COUNT):
                    dns_worker = DNSWorker(self._BLACKLIST_DNS, self._DNS_SERVER_IP, localhost_socket, self._queue)
                    dns_worker_process = multiprocessing.Process(target=dns_worker.start_worker, args=())
                    dns_worker_process.start()
                    dns_processes.append(dns_worker_process)
            for dns_process in dns_processes:
                dns_process.join()
        except Exception:
            self._logger.error('Something happend!', exc_info=True)

    def _setup_worker(self):
        self._logger = logging.getLogger()

    def get_log_reader(self):
        return self._queue
