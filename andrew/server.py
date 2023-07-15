import argparse
import socket

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--power', type=float, required=False, default=64,
                    help='servers processing power, kiloBytes/s')
args = parser.parse_args()

# HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
HOST = '0.0.0.0'
PORT = 49420  # Port to listen for data/client nodes

power_kBps = args.power

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
    listener.bind((HOST, PORT))
    listener.listen()
    # while True:
    conn, addr = listener.accept()
    with conn:  # TODO: spawn a thread
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(bytes(str(power_kBps), encoding='utf8'))
