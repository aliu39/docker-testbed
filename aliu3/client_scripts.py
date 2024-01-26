"""
Avoid the problem of having to copy python files to every client on setup, unlike server.py
"""

def make_request_power_script(sock_timeout_s, server_ip, server_port):
    return f"""import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout({sock_timeout_s})
    sock.connect(('{server_ip}', {server_port}))
    sock.sendall(b'POWER REQUEST')
    power = float(sock.recv(1024).decode('utf-8'))
    print('POWER:', power)"""

def make_send_data_script(sock_timeout_s, server_ip, server_port, data_size_mb):
    return f"""import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout({sock_timeout_s})
    sock.connect(('{server_ip}', {server_port}))
    sock.sendall(b'DATA\\n{data_size_mb} MB\\n')
    for _ in range(int({data_size_mb} * 1e6)):
        sock.sendall(b'A' * 1000)
    while sock.recv(1024):
        pass
    print('FINISHED: streamed {data_size_mb} MB')"""
