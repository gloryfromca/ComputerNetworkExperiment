import socket
import struct
from socketserver import StreamRequestHandler, ThreadingTCPServer

from SOCKS5 import exceptions
from utils import exchange_data


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

        remote = None
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

        if remote and reply[1] == 0:
            exchange_data(self.connection, remote)
        self.server.close_request(self.request)

    def reply_failed(self, address_type, error_number):
        return struct.pack("!BBBBIH", self.SOCKS_VERSION, error_number, 0, address_type, 0, 0)

    def parse_address(self, address_type):
        if address_type == 1:
            address = socket.inet_ntoa(self.connection.recv(4))
        elif address_type == 3:
            domain_length = ord(self.connection.recv(1))
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
    # curl -v --socks5 127.0.0.1:2019 https://www.baidu.com
    # chrome中使用SwitchyOmega插件不work，但是firefox设置代理之后很work，可能是协议实现不全
    server = ThreadingTCPServer(('0.0.0.0', 2019), SOCKS5RequestHandler)
    server.serve_forever()
