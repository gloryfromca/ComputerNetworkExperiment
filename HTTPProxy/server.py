from flask import Flask, request, Response
import requests
import gzip
import io

# app run使用Response默认用HTTP 1.0, 需要修改为HTTP 1.1, 不然无法支持转发chunked的http请求
from http.server import BaseHTTPRequestHandler
BaseHTTPRequestHandler.protocol_version = "HTTP/1.1"

http_proxy = Flask(__name__)


def gz_decode(data):
    # 用来解压gzip
    compressed_stream = io.BytesIO(data)
    gziper = gzip.GzipFile(fileobj=compressed_stream)
    data2 = gziper.read()
    return data2


@http_proxy.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@http_proxy.route("/<path:path>", methods=["GET", "POST"])
def proxy(path):
    def show_error(e):
        print("ERROR:")
        print(method, host, headers)
        print(e)

    host = request.url
    method = request.method
    headers = dict(request.headers)

    # 代理不能转发Connection首部
    # https://www.cnblogs.com/selol/p/5446965.html
    if "Proxy-Connection" in headers:
        headers["Connection"] = headers["Proxy-Connection"]

    try:
        # 为什么stream=True?
        # 因为gzip会默认被解压，转发到client的时候，response的header会使得客户端再次解压缩，肯定直接报错
        # 这里stream=True可以拿到
        # https://www.cnblogs.com/lilinwei340/p/7227579.html
        current_response = requests.request(method, host, headers=headers, stream=True)
        current_response_raw = current_response.raw

        response_headers = [(key, value) for key, value in current_response_raw.headers.items()]
        response_headers.append(("Proxy-Demo", "OK"))

        raw_content = current_response_raw.read()

        # raw的body虽然还是压缩状态，但是chunks还是被合并了,重新构建一个chunk
        # https://yq.aliyun.com/articles/42170
        is_chunked = current_response_raw.headers.get("Transfer-Encoding") == "chunked"
        if is_chunked:
            raw_content = hex(len(raw_content))[2:].encode('utf-8') + b"\r\n" + raw_content + b"\r\n" + b"0\r\n\r\n"
        result = Response(raw_content,
                          status=current_response_raw.status,
                          headers=response_headers)
        if is_chunked:

            result.headers.pop("Content-Length")
            result.automatically_set_content_length = False
        return result
    except ConnectionError:
        return Response("Connection Error", status=500)
    except Exception as e:
        show_error(e)
        return Response("Other Error", status=500)


if __name__ == "__main__":
    # curl -v -x http://127.0.0.1:8000 http://cpro.baidustatic.com/cpro/logo/css/logo-sm.css
    http_proxy.run("0.0.0.0", 8000)
