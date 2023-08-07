import argparse
import socket
import threading

# HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
HOST = '0.0.0.0'
PORT = 49420  # Port to listen for data/client nodes

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--power', type=float, required=False, default=16,
                        help='servers processing power, megaBytes/s')
    args = parser.parse_args()

    POWER_MBPS = args.power

    clients = dict()  # addr -> conn TODO: store more fields? a thread? use an id?
    total_load = 0
    clients_lock = threading.Lock()

    def handle_conn(conn, addr):
        global total_load

        clients_lock.acquire()
        clients[addr] = {'conn': conn}
        clients_lock.release()

        bytes_expected = 0
        with conn:
            while True:
                in_msg = conn.recv(max(bytes_expected, 1024))
                if not in_msg:
                    break

                if bytes_expected:  # interpret as data
                    bytes_expected = max(bytes_expected - len(in_msg), 0)
                    conn.sendall(in_msg)  # echo data

                    clients_lock.acquire()
                    clients[addr]['load'] -= len(in_msg)
                    total_load -= len(in_msg)
                    clients_lock.release()
                    # TODO: make a way to cancel data transfer?
                    continue

                in_msg = in_msg.decode('utf8')
                if in_msg == 'POWER REQUEST':
                    clients_lock.acquire()
                    n_clients = len(clients)
                    if n_clients == 0:  # avoid fatal error
                        print('server error: zero clients while handling power request')
                        n_clients = 1
                    clients_lock.release()
                    conn.sendall(bytes(str(POWER_MBPS / n_clients), encoding='utf8'))

                elif in_msg.startswith('DATA'):
                    lines = in_msg.split('\n')
                    [bytes_expected, unit] = lines[1].split()
                    bytes_expected = float(bytes_expected)
                    unit = unit.lower()
                    if unit == 'kb':
                        bytes_expected *= 1e3
                    elif unit == 'mb':
                        bytes_expected *= 1e6
                    elif unit == 'gb':
                        bytes_expected *= 1e9
                    elif unit != 'b':
                        print(f'server warning: unexpected data unit {unit}')

                    # track load in clients
                    clients_lock.acquire()
                    clients[addr]['load'] = bytes_expected
                    total_load += bytes_expected
                    clients_lock.release()

                else:
                    print(f'server error: unexpected message {in_msg[:min(len(in_msg), 100)]}')

            clients_lock.acquire()
            del clients[addr]
            clients_lock.release()


    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((HOST, PORT))
        listener.listen()
        while True:
            conn, addr = listener.accept()
            x = threading.Thread(target=handle_conn, args=(conn, addr))
            x.start()
