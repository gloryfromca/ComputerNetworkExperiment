import socket
from socketserver import ThreadingTCPServer
from http.server import BaseHTTPRequestHandler
from utils import exchange_data, ENABLE_HTTP_1_1


class HTTPTunnelRequestHandler(BaseHTTPRequestHandler):

    def do_CONNECT(self):
        host_port = self.headers.get("HOST").split(":")
        address = host_port[0]
        port = int(host_port[1]) if len(host_port) == 2 else 443

        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote.connect((address, port))
        self.connection.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        exchange_data(self.connection, remote)
        self.server.close_request(self.request)


if __name__ == "__main__":
    # PYTHONPATH=. python HTTPTunnel/server.py
    # curl -v -x 127.0.0.1:7999 https://www.baidu.com
    server = ThreadingTCPServer(('0.0.0.0', 7999), HTTPTunnelRequestHandler)
    server.serve_forever()
