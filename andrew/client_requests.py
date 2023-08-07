

def power_request(sock_timeout_s, server_ip, server_port):
    return f"""import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout({sock_timeout_s})
    sock.connect(('{server_ip}', {server_port}))
    sock.sendall(b'POWER REQUEST')
    power = float(sock.recv(1024).decode('utf-8'))
    print('POWER:', power)"""



