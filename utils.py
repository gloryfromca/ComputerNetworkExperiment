import select
import gzip
import io

# app run使用Response默认用HTTP 1.0, 需要修改为HTTP 1.1, 不然无法支持转发chunked的http请求
from http.server import BaseHTTPRequestHandler
BaseHTTPRequestHandler.protocol_version = "HTTP/1.1"
ENABLE_HTTP_1_1 = True


def exchange_data(client, remote):
    while True:
        # 连接断开之类的异常报错处理省略掉
        rs, ws, es = select.select([client, remote], [], [])
        if client in rs:
            data = client.recv(4096)
            print("client:", data)
            if remote.send(data) <= 0:
                break
        if remote in rs:
            data = remote.recv(4096)
            print("remote:", data)
            if client.send(data) <= 0:
                break


def gz_decode(data):
    # 用来解压gzip
    compressed_stream = io.BytesIO(data)
    gziper = gzip.GzipFile(fileobj=compressed_stream)
    data2 = gziper.read()
    return data2
