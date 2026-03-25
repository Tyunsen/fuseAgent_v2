import getpass
import os
import select
import socket
import socketserver
import sys
import threading
import time

import paramiko


REMOTE_HOST = "211.87.232.112"
REMOTE_USERNAME = "jyzhu"
REMOTE_BIND_HOST = "127.0.0.1"
REMOTE_WEB_PORT = 36130
REMOTE_API_PORT = 36180
PREFERRED_LOCAL_WEB_PORT = 46130
PREFERRED_LOCAL_API_PORT = 46180


def find_free_port(preferred_port: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", preferred_port))
            return preferred_port
        except OSError:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]


class ForwardServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class Handler(socketserver.BaseRequestHandler):
    remote_host = None
    remote_port = None
    transport = None

    def handle(self):
        try:
            channel = self.transport.open_channel(
                "direct-tcpip",
                (self.remote_host, self.remote_port),
                self.request.getpeername(),
            )
        except Exception as exc:
            print(
                f"failed to open tunnel to {self.remote_host}:{self.remote_port}: {exc}",
                file=sys.stderr,
            )
            return

        if channel is None:
            print(
                f"ssh tunnel to {self.remote_host}:{self.remote_port} was rejected",
                file=sys.stderr,
            )
            return

        try:
            while True:
                read_ready, _, _ = select.select([self.request, channel], [], [])
                if self.request in read_ready:
                    data = self.request.recv(1024)
                    if len(data) == 0:
                        break
                    channel.sendall(data)
                if channel in read_ready:
                    data = channel.recv(1024)
                    if len(data) == 0:
                        break
                    self.request.sendall(data)
        finally:
            channel.close()
            self.request.close()


def make_handler(transport, remote_host: str, remote_port: int):
    class SubHandler(Handler):
        pass

    SubHandler.transport = transport
    SubHandler.remote_host = remote_host
    SubHandler.remote_port = remote_port
    return SubHandler


def start_forward_server(transport, local_port: int, remote_port: int):
    server = ForwardServer(
        ("127.0.0.1", local_port),
        make_handler(transport, REMOTE_BIND_HOST, remote_port),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def connect_client(password: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        REMOTE_HOST,
        username=REMOTE_USERNAME,
        password=password,
        timeout=20,
    )
    return client


def main() -> int:
    password = os.environ.get("FUSEAGENT_REMOTE_SSH_PASSWORD") or getpass.getpass(
        f"SSH password for {REMOTE_USERNAME}@{REMOTE_HOST}: "
    )
    local_web_port = find_free_port(PREFERRED_LOCAL_WEB_PORT)
    local_api_port = find_free_port(PREFERRED_LOCAL_API_PORT)

    client = connect_client(password)
    transport = client.get_transport()
    if transport is None or not transport.is_active():
        print("ssh transport is not active", file=sys.stderr)
        return 1

    web_server = start_forward_server(transport, local_web_port, REMOTE_WEB_PORT)
    api_server = start_forward_server(transport, local_api_port, REMOTE_API_PORT)

    print("remote fuseAgent tunnel is ready")
    print(f"web: http://127.0.0.1:{local_web_port}/")
    print(f"api: http://127.0.0.1:{local_api_port}/docs")
    print("press Ctrl+C to stop")

    try:
        while transport.is_active():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        web_server.shutdown()
        web_server.server_close()
        api_server.shutdown()
        api_server.server_close()
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
