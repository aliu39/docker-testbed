"""
Given a list of server IPs, selects the best server to send data to for processing.
Does this using pathneck measurements and requesting each server for a processing power.
"""

import argparse
import ast
import socket
import traceback
from collections import defaultdict

from utils.experiment_helpers import pathneck, parse_pathneck_result

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--client', type=str, required=True,
                    help='(name, ip) of client node')
parser.add_argument('-d', '--data-size', type=float, required=False, default=200,
                    help='size of client data in KB (default 200)')
parser.add_argument('-s', '--server-ips', type=str, required=True,
                    help='list of server ips for data node to connect to')
args = parser.parse_args()

(client_name, client_ip) = ast.literal_eval(args.client)
data_size_kB = args.data_size
server_ips = ast.literal_eval(args.server_ips)
server_info = defaultdict(dict)  # key is server ip

PROCESS_POWER_PORT = 49420
SOCK_TIMEOUT_S = 1

best_server_ip, min_process_t = None, float('inf')
for ip in server_ips:

    # try to reach server and request processing power, via TCP
    power = None  # kiloBytes/s, not kilobits
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(SOCK_TIMEOUT_S)
            sock.connect((ip, PROCESS_POWER_PORT))
            sock.sendall(b'Request power')
            power = float(sock.recv(1024).decode('utf-8'))
    except:
        traceback.print_exc()

    if power is None:
        continue

    # measure bottleneck
    pathneck_result = pathneck(client_name, ip)
    print(pathneck_result)

    bottleneck_link, bottleneck_bw = None, None
    min_bw_link, min_bw = None, float('inf')
    prev_hop = client_ip
    for line in pathneck_result.splitlines():
        line = line.split()
        if len(line) == 8:
            ip, bw = line[2], float(line[6])
            if line[5] == '1':
                bottleneck_link, bottleneck_bw = (prev_hop, ip), bw
                break
            elif bw < min_bw:
                min_bw_link, min_bw = (prev_hop, ip), bw
            prev_hop = ip

    # default to minimum bw measurement # TODO:
    if bottleneck_link is None and min_bw_link is not None:
        bottleneck_link, bottleneck_bw = min_bw_link, min_bw

    process_t = data_size_kB * (1./power + 2./bottleneck_bw)
    if process_t < min_process_t:
        best_server_ip = ip
        min_process_t = process_t

    # store measurements
    server_info[ip]['bottleneck_link'] = bottleneck_link
    server_info[ip]['bottleneck_bw'] = bottleneck_bw
    server_info[ip]['process_power_kBps'] = power

print(server_info)
print(best_server_ip, min_process_t)
