import socket
import socks
import requests

## pip install PySocks
socks.set_default_proxy(socks.SOCKS5, "localhost", 2019)
socket.socket = socks.socksocket

test_url = 'https://baidu.com'
html = requests.get(test_url, timeout=8)
html.encoding = 'utf-8'
print(html.content)
