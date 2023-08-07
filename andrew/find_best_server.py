"""
Given a list of server IPs, selects the best server to send data to for processing.
Does this using pathneck measurements and requesting each server for a processing power.
"""

import argparse
import ast
import os
import socket
import subprocess
import time
import traceback
from collections import defaultdict

from utils.experiment_helpers import pathneck, parse_pathneck_result, ping, iperf_server, iperf_client_bw, iperf_client
from andrew.server import PORT as SERVER_PORT
from andrew.client_requests import power_request

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--client', type=str, required=True,
                    help='(name, ip) of client node')
parser.add_argument('-d', '--data-size', type=float, required=False, default=100,
                    help='size of client data in MB (default 100)')
parser.add_argument('-s', '--servers', type=str, required=True,
                    help='list of servers (name, ip) for data node to connect to')
parser.add_argument('-cc', '--contesting_clients', type=str, required=False, default='[]',
                    help='list of contesting clients (name, target_server_ip) for generating background traffic')
parser.add_argument('--iperf', action='store_true', help='use iperf to measure bandwidth instead of pathneck')
args = parser.parse_args()

(client, client_ip) = ast.literal_eval(args.client)
data_size_mb = args.data_size
servers = ast.literal_eval(args.servers)
server_info = defaultdict(dict)  # key is server ip
contesting_clients = ast.literal_eval(args.contesting_clients)
use_iperf = args.iperf

SOCK_TIMEOUT_S = 10
MbPS_TO_MBPS = 1/8

# start background traffic from contesting clients
for server, _ in servers:
    iperf_server(server)

# contesting_clients = [
#     ('c3', '10.0.4.5'),  # ip is for target SERVER
#     ('c4', '10.0.3.5'),
# ]
for c, server_ip in contesting_clients:
    iperf_client(c, server_ip)

# find best server
best_server_ip, min_process_t = None, float('inf')
for server, _ in servers:
    # start server program to listen for processing power requests
    subprocess.Popen(['docker', 'exec', server, 'python3', 'server.py'])

for server, ip in servers:
    # try to reach server and request processing power, via TCP
    power = None  # note: megaByte/s, not megabits
    try:
        power_request_code = power_request(SOCK_TIMEOUT_S, ip, SERVER_PORT)
        result = subprocess.run(['docker', 'exec', client, 'python3', '-c', power_request_code], stdout=subprocess.PIPE)
        for line in result.stdout.decode('utf-8').splitlines():
            if 'POWER' in line:
                power = float(line.split(':')[1])
                break
    except:
        traceback.print_exc()

    print(f'---{server} POWER={power}---')
    if power is None:
        continue

    if use_iperf:
        bottleneck_bw = iperf_client_bw(client, ip)
        bottleneck_link = None

    else:  # use PATHNECK
        retcode, result = pathneck(client, ip)
        print(retcode, result)

        bottleneck_link, bottleneck_bw = None, None
        min_bw_link, min_bw = None, float('inf')
        prev_hop = client_ip
        for line in result.splitlines():
            line = line.split()
            if len(line) == 8:
                curr_hop, bw = line[2], float(line[6])
                if line[5] == '1':
                    bottleneck_link, bottleneck_bw = (prev_hop, curr_hop), bw
                    break
                elif bw < min_bw:
                    min_bw_link, min_bw = (prev_hop, curr_hop), bw
                prev_hop = curr_hop

        # default to minimum bw measurement if no bottleneck found  #TODO: verify this is an appropriate estimate
        if bottleneck_link is None and min_bw_link is not None:
            bottleneck_link, bottleneck_bw = min_bw_link, min_bw

    # estimate processing time
    process_t = data_size_mb * (1. / (power*1000) + 2. / (bottleneck_bw * MbPS_TO_MBPS))
    if process_t < min_process_t:
        best_server_ip = ip
        min_process_t = process_t

    # store measurements
    # server_info[ip]['bottleneck_link'] = bottleneck_link
    server_info[ip]['bottleneck_bw'] = bottleneck_bw
    server_info[ip]['process_power'] = power
    server_info[ip]['power_unit'] = 'MB/s'

for c, _ in contesting_clients:
    os.system(f"docker exec {c} pkill iperf")
for server, _ in servers:
    os.system(f"docker exec {server} pkill iperf")
    os.system(f"docker exec {server} pkill python3")

time.sleep(3)

print('------------------------------------------------')
print(server_info)
print(best_server_ip, 'estimated processing time (s) =', min_process_t)
