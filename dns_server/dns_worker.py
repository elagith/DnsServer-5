import logging
import logging.config
import logging.handlers
import json
import socket

from core.pipe_handler import PipeHandler
from dnslib import DNSRecord, RR, QTYPE, A


class DNSWorker:
    _DNS_PORT = 53

    def __init__(self, blacklist_dns, dns_server_ip, dns_socket, pipe):
        self.pipe = pipe
        self._logger = None
        self._DNS_SERVER_IP = dns_server_ip
        self._BLACKLIST_DNS = blacklist_dns
        self._DNS_SOCKET = dns_socket

    def start_worker(self):
        self._setup_worker()
        self._listen_to_requests()

    def _setup_worker(self):
        with open(__package__ + '\config.json') as config_file:
            data = json.load(config_file)
        logging.config.dictConfig(data['logging'])
        self._logger = logging.getLogger(__name__)

        qh = PipeHandler(self.pipe)
        self._logger.addHandler(qh)

    def _listen_to_requests(self):
        self._logger.info('Starting listening to local requests')
        while True:
            try:
                raw_data, addr = self._DNS_SOCKET.recvfrom(512)
                self._handle_dns_query(raw_data, addr, self._DNS_SOCKET)
            except ConnectionResetError:
                pass
            except Exception:
                self._logger.fatal('Something happend', exec_info=True)
                exit()

    def _handle_dns_query(self, raw_data, addr, localhost_socket):
        dns_query = DNSRecord.parse(raw_data)
        self._logger.debug('handling id - ' + hex(dns_query.header.id))
        if self._is_blacklist(dns_query):
            self._replay_dns_none(addr, dns_query, localhost_socket)
            return
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as dns_socket:
            for host_query in dns_query.questions:
                pass
                self._logger.info('request dns - ' + str(host_query.qname))
            dns_socket.sendto(raw_data, (self._DNS_SERVER_IP, self._DNS_PORT))
            dns_reply = self._catch_dns_answer(dns_query.header.id, dns_socket)
            localhost_socket.sendto(dns_reply.pack(), addr)
            return

    def _is_blacklist(self, dns_query):
        for host_query in dns_query.questions:
            return len(list(filter(lambda x: x in str(host_query.qname), self._BLACKLIST_DNS))) > 0

    def _replay_dns_none(self, addr, dns_query, localhost_socket):
        dns_reply = dns_query.reply()
        for host_query in dns_query.questions:
            self._logger.info('Blacklist DNS request - ' + str(host_query.qname))
            dns_reply.add_answer(RR(str(host_query.qname), QTYPE.A, rdata=A("0.0.0.0"), ttl=60))
        localhost_socket.sendto(dns_reply.pack(), addr)

    def _catch_dns_answer(self, dns_request_id, dns_socket):
        while True:
            raw_data, addr = dns_socket.recvfrom(4096)
            dns_query = DNSRecord.parse(raw_data)
            if dns_query.header.id == dns_request_id:
                return dns_query