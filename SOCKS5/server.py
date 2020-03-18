import select
import socket
import struct
from socketserver import StreamRequestHandler, ThreadingTCPServer

from SOCKS5 import exceptions


class SOCKS5RequestHandler(StreamRequestHandler):
    SOCKS_VERSION = 5

    def handle(self):
        header = self.connection.recv(2)
        version, n_methods = struct.unpack("!BB", header)
        self.check_version(version)
        methods = self.is_available(n_methods)
        if 0 not in set(methods):
            self.server.close_request(self.request)
            return

        self.connection.sendall(struct.pack("!BB", version, 0))

        version, cmd, _, address_type = struct.unpack("!BBBB", self.connection.recv(4))
        self.check_version(version)
        address = self.parse_address(address_type)
        port = struct.unpack('!H', self.connection.recv(2))[0]

        try:
            if cmd == 1:
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.connect((address, port))
                bind_address = remote.getsockname()
            else:
                self.server.close_request(self.request)
                raise exceptions.UnsupportedCMD()
            addr = struct.unpack("!I", socket.inet_aton(bind_address[0]))[0]
            port = bind_address[1]
            reply = struct.pack("!BBBBIH", self.SOCKS_VERSION, 0, 0, address_type, addr, port)
        except Exception as e:
            print(e)
            reply = self.reply_failed(address_type, 5)
        self.connection.sendall(reply)

        if reply[1] == 0 and cmd == 1:
            self.exchange_data(self.connection, remote)
        self.server.close_request(self.request)

    def exchange_data(self, client, remote):
        while True:
            rs, ws, es = select.select([client, remote], [], [])
            if client in rs:
                data = client.recv(4096)
                if remote.send(data) <= 0:
                    break
            if remote in rs:
                data = remote.recv(4096)
                if client.send(data) <= 0:
                    break

    def reply_failed(self, address_type, error_number):
        return struct.pack("!BBBBIH", self.SOCKS_VERSION, error_number, 0, address_type, 0, 0)

    def parse_address(self, address_type):
        if address_type == 1:
            address = socket.inet_ntoa(self.connection.recv(4))
        elif address_type == 3:
            domain_length = ord(self.connection.recv(1)[0])
            address = self.connection.recv(domain_length).decode("ascii")
        else:
            raise exceptions.UnsupportedAddressFormat()
        return address

    def check_version(self, version):
        if version != self.SOCKS_VERSION:
            raise exceptions.UnSupportedVersion()

    def is_available(self, n_methods):
        methods = []
        for i in range(n_methods):
            methods.append(ord(self.connection.recv(1)))
        return methods


if __name__ == "__main__":
    # PYTHONPATH=. python SOCKS5/server.py
    server = ThreadingTCPServer(('0.0.0.0', 2019), SOCKS5RequestHandler)
    server.serve_forever()
