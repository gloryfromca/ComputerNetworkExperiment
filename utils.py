import select


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
