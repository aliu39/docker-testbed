"""
Server program to run from a container/node. Accepts TCP connections and two
types of requests:
1) 'POWER REQUEST': respond with server's current processing power in megabytes/s
-> TODO: make this vary according to some schedule, num connected clients, load, etc

2) 'DATA\n[x] [unit][\noptional data]': echos the data back, and updates global client dict with
the client "load" (nbytes still expected from the client).
-> server will read ALL future TCP messages as data, until bytes_expected is read
-> Can be used to create traffic over the testbed topology, simulating large, concurrent data transfers

NEEDS TO BE COPIED TO DOCKER CONTAINERS AND RAN ON STARTUP (modified docker image and setup.py)
"""
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

    # globals
    POWER_MBPS = args.power # constant
    clients = dict()  # addr -> attrs dict. 'conn' and 'load' (remaining bytes_expected) #TODO: store more fields? thread obj? id?
    total_load = 0
    clients_lock = threading.Lock()

    # run in a thread to serve 1 client (request/response loop that runs until client closes connection)
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
                    clients_lock.acquire()
                    clients[addr]['load'] -= len(in_msg)
                    total_load -= len(in_msg)
                    clients_lock.release()

                    conn.sendall(in_msg)  # echo data
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
                    # header
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
                    bytes_expected = int(bytes_expected)

                    # track remaining load for each client (field is UNUSED)
                    clients_lock.acquire()
                    clients[addr]['load'] = bytes_expected
                    total_load += bytes_expected
                    clients_lock.release()
                    
                    # payload
                    if len(lines) > 2:
                        in_msg = ''.join(lines[2:])
                        bytes_expected = max(bytes_expected - len(in_msg), 0)
                        clients_lock.acquire()
                        clients[addr]['load'] -= len(in_msg)
                        total_load -= len(in_msg)
                        clients_lock.release()
                        conn.sendall(bytes(in_msg, encoding='utf8'))  # echo data

                else:
                    print(f'server error: unexpected message {in_msg[:min(len(in_msg), 100)]}')

            clients_lock.acquire()
            del clients[addr]
            clients_lock.release()

    # listen/accept loop
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((HOST, PORT))
        listener.listen()
        while True:
            conn, addr = listener.accept()
            x = threading.Thread(target=handle_conn, args=(conn, addr))
            x.start()
